from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import re
from app.database.db import get_connection
from app.ai.gemini_service import parse_trip_prompt
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


@router.post("/ai/recommend", status_code=status.HTTP_200_OK)
def recommend(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    try:
        # Try parsing with Gemini first, fall back to local parsing on any failure
        source = "gemini"
        try:
            prefs = parse_trip_prompt(request.prompt)
            # Validate essential fields are present in the response dict
            for key in ["days", "budget", "members", "vibe"]:
                if key not in prefs:
                    raise KeyError(f"Missing key: {key}")
        except Exception:
            prefs = fallback_parse_prompt(request.prompt)
            source = "fallback"

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM destinations")
        rows = cur.fetchall()

        results = []
        target_vibe = str(prefs.get("vibe", "chill")).lower()
        budget = float(prefs.get("budget", 50000))
        days = int(prefs.get("days", 1))
        members = int(prefs.get("members", 1))

        for r in rows:
            score = 0

            dest_id = r[0]
            name = r[1]
            description = r[2]
            lat = r[3]
            lng = r[4]
            cost = float(r[5]) if r[5] is not None else 0.0
            vibes = str(r[6]).lower() if r[6] is not None else ""
            rating = float(r[7]) if r[7] is not None else 0.0

            # Vibe matching
            if target_vibe and target_vibe in vibes:
                score += 20

            # Boost scores for individual vibes mentioned in original user prompt
            user_prompt_lower = request.prompt.lower()
            if "beach" in user_prompt_lower and "beach" in vibes:
                score += 5
            if "nature" in user_prompt_lower and "nature" in vibes:
                score += 5
            if "adventure" in user_prompt_lower and "adventure" in vibes:
                score += 5
            if "relax" in user_prompt_lower and "relax" in vibes:
                score += 5
            if "chill" in user_prompt_lower and "chill" in vibes:
                score += 5

            # Budget evaluation (cost per day per member vs total budget)
            total_est_cost = cost * days * members
            if total_est_cost <= budget:
                score += 15
            elif cost <= budget:
                score += 5

            # Rating boost
            score += rating * 2

            results.append({
                "id": dest_id,
                "name": name,
                "description": description,
                "lat": lat,
                "lng": lng,
                "cost": cost,
                "vibes": vibes,
                "rating": rating,
                "score": round(score, 2)
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