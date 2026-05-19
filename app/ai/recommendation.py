from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import re
from app.database.db import get_connection
from app.ai.gemini_service import parse_trip_prompt, generate_hybrid_recommendations
from app.auth.dependencies import get_current_user_optional

router = APIRouter()


class RecommendationRequest(BaseModel):
    prompt: str


def fallback_parse_prompt(prompt: str) -> dict:
    prompt_lower = prompt.lower()
    
    # Extract days
    days_match = re.search(r"\b(\d+)\s*day", prompt_lower)
    days = int(days_match.group(1)) if days_match else 1
    
    # Extract members/people
    members_match = re.search(r"\b(\d+)\s*(?:pax|people|member|person|head|group)", prompt_lower)
    members = int(members_match.group(1)) if members_match else 1
    
    # Extract budget
    budget = 50000.0  # Default budget
    # Look for patterns like "budget of 10000", "php 5000", "5000 pesos", "10k budget", "around 3000"
    budget_match = re.search(r"(?:budget|php|₱|peso|pesos|cost|price|max|around|approx(?:ately)?)\s*(?:of|is|at)?\s*(\d+[\d,]*)\s*(k)?\b", prompt_lower)
    
    if not budget_match:
        # Also check for "10k" or "5k" directly
        budget_match = re.search(r"\b(\d+[\d,]*)\s*(k)\b", prompt_lower)
        
    if not budget_match:
        # Fall back to any large number >= 100
        budget_match = re.search(r"\b(\d{3,}[\d,]*)\b", prompt_lower)
        
    if budget_match:
        val_str = budget_match.group(1).replace(",", "")
        try:
            val = float(val_str)
            # Handle "k" suffix if present
            if len(budget_match.groups()) >= 2 and budget_match.group(2) == 'k':
                val *= 1000
            budget = val
        except ValueError:
            pass
            
    # Extract vibe
    vibe = "chill"
    vibes_list = ["beach", "nature", "adventure", "relax", "chill", "luxury", "urban", "food", "educational"]
    for v in vibes_list:
        if v in prompt_lower:
            vibe = v
            break
            
    return {
        "days": days,
        "budget": budget,
        "members": members,
        "vibe": vibe
    }


def calculate_local_destination_score(dest: dict, days: int, budget: float, members: int, target_vibe: str, prompt: str) -> float:
    """
    Performs a deep structural matching and pricing calculation to score a destination.
    Evaluates dynamic pricing (entrance fees, elective activities, accommodations), 
    accessibility requirements (kids, seniors, wheelchairs, pets), and vibes.
    """
    score = 0.0
    user_prompt_lower = prompt.lower()
    
    # 1. Vibe & Category Matching (up to 25 points)
    vibes_lower = dest["vibes"].lower()
    categories_lower = dest["category"].lower() if dest.get("category") else ""
    
    if target_vibe and (target_vibe in vibes_lower or target_vibe in categories_lower):
        score += 15
        
    for v in ["beach", "nature", "adventure", "relax", "chill", "luxury", "urban", "food", "educational", "historic", "waterfalls", "family"]:
        if v in user_prompt_lower and (v in vibes_lower or v in categories_lower):
            score += 3
            
    # 2. Rating baseline boost (up to 10 points)
    score += dest["rating"] * 2
    
    # 3. Accessibility & Companion Requirements (up to 20 points)
    has_kids = any(word in user_prompt_lower for word in ["kid", "child", "children", "baby", "infant", "toddler", "family"])
    has_elderly = any(word in user_prompt_lower for word in ["elderly", "parent", "grandparent", "senior", "old", "father", "mother", "mom", "dad"])
    has_wheelchair = any(word in user_prompt_lower for word in ["wheelchair", "disabled", "accessible", "disability", "pwd"])
    has_pets = any(word in user_prompt_lower for word in ["pet", "dog", "cat", "animal"])
    
    if has_kids and dest["is_kid_friendly"]:
        score += 10
    if has_elderly and dest["is_elderly_friendly"]:
        score += 5
    if has_wheelchair and dest["is_wheelchair_accessible"]:
        score += 15
    if has_pets and dest["is_pet_friendly"]:
        score += 5

    # 4. Detailed Financial Cost Model & Comparison (up to 45 points)
    # Estimate dynamic entry costs
    entrance_fee_val = 0.0
    ent_str = dest["entrance_fee"]
    if ent_str and "free" not in ent_str.lower():
        num_match = re.search(r"(\d+[\d,]*)", ent_str.replace(",", ""))
        if num_match:
            entrance_fee_val = float(num_match.group(1))
            
    total_entrance = entrance_fee_val * members
    
    # Parse accommodations list to find the optimal lodging tier fitting our daily budget
    accomm_price_val = 0.0
    try:
        if dest["accommodations"]:
            accoms = json.loads(dest["accommodations"]) if isinstance(dest["accommodations"], str) else dest["accommodations"]
            if accoms:
                # daily lodging allocation: (budget - entrance fees) / days
                target_room_budget = (budget - total_entrance) / max(1, days)
                
                # Choose standard or best fitting budget option
                fitting_room = None
                min_diff = float('inf')
                for room in accoms:
                    room_price = float(room["price"].replace(",", ""))
                    if room_price <= target_room_budget:
                        diff = target_room_budget - room_price
                        if diff < min_diff:
                            min_diff = diff
                            fitting_room = room_price
                
                if fitting_room is not None:
                    accomm_price_val = fitting_room
                else:
                    cheapest = min(float(r["price"].replace(",", "")) for r in accoms)
                    accomm_price_val = cheapest
    except Exception:
        pass
        
    total_lodging = accomm_price_val * max(0, days - 1)
    if total_lodging == 0 and days > 0:
        overnight_str = dest["overnight_fee"]
        if overnight_str and "free" not in overnight_str.lower():
            num_match = re.search(r"(\d+[\d,]*)", overnight_str.replace(",", ""))
            if num_match:
                total_lodging = float(num_match.group(1)) * max(0, days - 1)

    # Estimate activities costs (average first 2 elective experiences)
    activities_cost = 0.0
    try:
        if dest["activity_prices"]:
            act_prices = json.loads(dest["activity_prices"]) if isinstance(dest["activity_prices"], str) else dest["activity_prices"]
            if act_prices:
                for act in act_prices[:2]:
                    act_val = float(act["price"].replace(",", ""))
                    if act.get("isPerPerson", True):
                        activities_cost += act_val * members
                    else:
                        activities_cost += act_val
    except Exception:
        pass

    # Food & local transit base allowance (₱300 per traveler per day)
    food_and_travel = 300.0 * members * days
    
    # Calculate complete estimated expenditures
    total_calculated_cost = total_entrance + total_lodging + activities_cost + food_and_travel
    
    # Budget Scoring Comparison:
    if total_calculated_cost <= budget:
        # Perfect fit within budget constraints
        score += 35
        # Give extra points if they are utilizing the budget efficiently (value score)
        if total_calculated_cost >= budget * 0.6:
            score += 10
    else:
        # Exceeds budget constraints - calculate overshoot percentage
        excess_ratio = total_calculated_cost / max(1.0, budget)
        if excess_ratio <= 1.2:
            score += 15  # Small penalty
        elif excess_ratio <= 1.5:
            score += 5   # Medium penalty
        else:
            score -= 10  # Major penalty for luxury options when budget is low

    return max(0.0, score)


import json

@router.post("/ai/recommend", status_code=status.HTTP_200_OK)
def recommend(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    try:
        # 1. Fetch all destinations from the database first
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM destinations")
        
        # Get column names to avoid hardcoded index lookups
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        # Format database rows into easy-to-use dicts
        db_destinations = []
        db_by_id = {}
        for r in rows:
            row_dict = dict(zip(colnames, r))
            dest = {
                "destination_id": row_dict["destination_id"],
                "name": row_dict["name"],
                "description": row_dict["description"] or "",
                "lat": row_dict["lat"],
                "lng": row_dict["lng"],
                "estimated_cost": float(row_dict["estimated_cost"]) if row_dict.get("estimated_cost") is not None else 0.0,
                "vibes": row_dict["vibes"] if row_dict.get("vibes") is not None else "",
                "rating": float(row_dict["rating"]) if row_dict.get("rating") is not None else 0.0,
                
                # Enriched fields
                "district": row_dict.get("district") or "",
                "image_url": row_dict.get("image_url") or "",
                "category": row_dict.get("category") or "",
                "location": row_dict.get("location") or "",
                "entrance_fee": row_dict.get("entrance_fee") or "",
                "overnight_fee": row_dict.get("overnight_fee"),
                "operating_hours": row_dict.get("operating_hours") or "",
                "activities": row_dict.get("activities"),
                "activity_prices": row_dict.get("activity_prices"),
                "accommodations": row_dict.get("accommodations"),
                "meal_inclusions": row_dict.get("meal_inclusions") or "",
                "travel_notes": row_dict.get("travel_notes") or "",
                "best_time_to_visit": row_dict.get("best_time_to_visit") or "",
                "how_to_get_there": row_dict.get("how_to_get_there") or "",
                "estimated_travel_time": row_dict.get("estimated_travel_time") or "",
                "what_to_bring": row_dict.get("what_to_bring"),
                "meal_plan_details": row_dict.get("meal_plan_details") or "",
                "is_kid_friendly": bool(row_dict.get("is_kid_friendly")),
                "is_wheelchair_accessible": bool(row_dict.get("is_wheelchair_accessible")),
                "is_pet_friendly": bool(row_dict.get("is_pet_friendly")),
                "is_elderly_friendly": bool(row_dict.get("is_elderly_friendly")),
            }
            db_destinations.append(dest)
            db_by_id[dest["destination_id"]] = dest

        results = []
        source = "gemini_hybrid"
        
        # Default empty preferences (will be extracted locally or populated by fallback)
        days = 1
        budget = 50000.0
        members = 1
        target_vibe = "chill"

        try:
            # 2. Try the Hybrid RAG AI recommendation first
            ai_recommendations = generate_hybrid_recommendations(request.prompt, db_destinations)
            
            # Map recommendations back to database objects
            for item in ai_recommendations:
                dest_id = item["destination_id"]
                if dest_id in db_by_id:
                    db_dest = db_by_id[dest_id]
                    
                    # Parse JSON fields safely
                    activities_list = []
                    try:
                        if db_dest["activities"]:
                            activities_list = json.loads(db_dest["activities"])
                    except Exception:
                        pass
                        
                    act_prices_list = []
                    try:
                        if db_dest["activity_prices"]:
                            act_prices_list = json.loads(db_dest["activity_prices"])
                    except Exception:
                        pass
                        
                    accomm_list = []
                    try:
                        if db_dest["accommodations"]:
                            accomm_list = json.loads(db_dest["accommodations"])
                    except Exception:
                        pass
                        
                    bring_list = []
                    try:
                        if db_dest["what_to_bring"]:
                            bring_list = json.loads(db_dest["what_to_bring"])
                    except Exception:
                        pass

                    results.append({
                        "id": dest_id,
                        "name": db_dest["name"],
                        # We use the custom, highly personalized explanation generated by the AI as description!
                        "description": item["match_reason"],
                        "original_description": db_dest["description"],
                        "lat": db_dest["lat"],
                        "lng": db_dest["lng"],
                        "cost": db_dest["estimated_cost"],
                        "vibes": db_dest["vibes"],
                        "rating": db_dest["rating"],
                        "score": round(item["score"], 2),
                        
                        # Return all detailed fields mapping exactly to Dart Destination model keys!
                        "district": db_dest["district"],
                        "image": db_dest["image_url"],
                        "category": [c.strip() for c in db_dest["category"].split(",") if c.strip()],
                        "location": db_dest["location"],
                        "entranceFee": db_dest["entrance_fee"],
                        "overnightFee": db_dest["overnight_fee"],
                        "operatingHours": db_dest["operating_hours"],
                        "activities": activities_list,
                        "activityPrices": act_prices_list,
                        "accommodations": accomm_list,
                        "mealInclusions": db_dest["meal_inclusions"],
                        "travelNotes": db_dest["travel_notes"],
                        "bestTimeToVisit": db_dest["best_time_to_visit"],
                        "howToGetThere": db_dest["how_to_get_there"],
                        "estimatedTravelTime": db_dest["estimated_travel_time"],
                        "whatToBring": bring_list,
                        "mealPlanDetails": db_dest["meal_plan_details"],
                        "accessibility": {
                            "isKidFriendly": db_dest["is_kid_friendly"],
                            "isWheelchairAccessible": db_dest["is_wheelchair_accessible"],
                            "isPetFriendly": db_dest["is_pet_friendly"],
                            "isElderlyFriendly": db_dest["is_elderly_friendly"]
                        }
                    })
            
            # Extract basic preferences from prompt using Gemini extraction as metadata
            try:
                prefs = parse_trip_prompt(request.prompt)
                days = int(prefs.get("days", 1))
                budget = float(prefs.get("budget", 50000.0))
                members = int(prefs.get("members", 1))
                target_vibe = str(prefs.get("vibe", "chill")).lower()
            except Exception:
                # Local regex backup for metadata extraction
                prefs = fallback_parse_prompt(request.prompt)
                days = prefs["days"]
                budget = prefs["budget"]
                members = prefs["members"]
                target_vibe = prefs["vibe"]

        except Exception as ai_err:
            # 3. Fallback: If Gemini API fails, compute score locally using original formula
            print(f"Gemini Hybrid RAG failed: {ai_err}. Falling back to local scoring.")
            source = "fallback"
            
            # Parse preferences locally
            prefs = fallback_parse_prompt(request.prompt)
            days = prefs["days"]
            budget = prefs["budget"]
            members = prefs["members"]
            target_vibe = prefs["vibe"]

            for dest in db_destinations:
                score = calculate_local_destination_score(dest, days, budget, members, target_vibe, request.prompt)

                # Parse JSON fields safely
                activities_list = []
                try:
                    if dest["activities"]:
                        activities_list = json.loads(dest["activities"])
                except Exception:
                    pass
                    
                act_prices_list = []
                try:
                    if dest["activity_prices"]:
                        act_prices_list = json.loads(dest["activity_prices"])
                except Exception:
                    pass
                    
                accomm_list = []
                try:
                    if dest["accommodations"]:
                        accomm_list = json.loads(dest["accommodations"])
                except Exception:
                    pass
                    
                bring_list = []
                try:
                    if dest["what_to_bring"]:
                        bring_list = json.loads(dest["what_to_bring"])
                except Exception:
                    pass

                results.append({
                    "id": dest["destination_id"],
                    "name": dest["name"],
                    "description": dest["description"],
                    "lat": dest["lat"],
                    "lng": dest["lng"],
                    "cost": dest["estimated_cost"],
                    "vibes": dest["vibes"],
                    "rating": dest["rating"],
                    "score": round(score, 2),
                    
                    # Return all detailed fields mapping exactly to Dart Destination model keys!
                    "district": dest["district"],
                    "image": dest["image_url"],
                    "category": [c.strip() for c in dest["category"].split(",") if c.strip()],
                    "location": dest["location"],
                    "entranceFee": dest["entrance_fee"],
                    "overnightFee": dest["overnight_fee"],
                    "operatingHours": dest["operating_hours"],
                    "activities": activities_list,
                    "activityPrices": act_prices_list,
                    "accommodations": accomm_list,
                    "mealInclusions": dest["meal_inclusions"],
                    "travelNotes": dest["travel_notes"],
                    "bestTimeToVisit": dest["best_time_to_visit"],
                    "howToGetThere": dest["how_to_get_there"],
                    "estimatedTravelTime": dest["estimated_travel_time"],
                    "whatToBring": bring_list,
                    "mealPlanDetails": dest["meal_plan_details"],
                    "accessibility": {
                        "isKidFriendly": dest["is_kid_friendly"],
                        "isWheelchairAccessible": dest["is_wheelchair_accessible"],
                        "isPetFriendly": dest["is_pet_friendly"],
                        "isElderlyFriendly": dest["is_elderly_friendly"]
                    }
                })

            results.sort(
                key=lambda x: x["score"],
                reverse=True
            )

        return {
            "message": "AI recommendations generated",
            "requested_by": current_user["email"] if current_user else "anonymous",
            "parsed_preferences": {
                "days": days,
                "budget": budget,
                "members": members,
                "vibe": target_vibe,
                "parser_source": source
            },
            "results": results[:5]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()