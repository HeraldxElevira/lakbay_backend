import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import typing

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")


def parse_trip_prompt(prompt: str):
    response = model.generate_content(f"""
    Extract travel preferences from this prompt.

    Return ONLY valid JSON:

    {{
        "days": number,
        "budget": number,
        "members": number,
        "vibe": "string"
    }}

    Prompt:
    {prompt}
    """)

    return json.loads(response.text)


class RecommendationItem(typing.TypedDict):
    destination_id: int
    score: float
    match_reason: str


def generate_hybrid_recommendations(prompt: str, db_destinations: list) -> list:
    """
    Evaluates database destinations against a user's prompt using Gemini 2.0.
    Selects and ranks the top 5 matching destinations and generates a custom match reason for each.
    """
    # Format candidates list to send to Gemini with all newly added rich details
    candidates_str = ""
    for dest in db_destinations:
        candidates_str += (
            f"ID: {dest['destination_id']} | Name: {dest['name']} | "
            f"Category: {dest['category']} | Vibes: {dest['vibes']} | Rating: {dest['rating']}\n"
            f"  Description: {dest['description']}\n"
            f"  Location: {dest['location']} | District: {dest['district']}\n"
            f"  Entrance Fee: {dest['entrance_fee']} | Overnight Fee: {dest['overnight_fee']} | Operating Hours: {dest['operating_hours']}\n"
            f"  Available Activities: {dest['activities']}\n"
            f"  Activity Prices: {dest['activity_prices']}\n"
            f"  Accommodation Options: {dest['accommodations']}\n"
            f"  Meal Inclusions: {dest['meal_inclusions']} | Meal Plan Details: {dest['meal_plan_details']}\n"
            f"  Accessibility: Kid-Friendly: {dest['is_kid_friendly']} | Wheelchair Accessible: {dest['is_wheelchair_accessible']} | Pet-Friendly: {dest['is_pet_friendly']} | Elderly-Friendly: {dest['is_elderly_friendly']}\n"
            f"  Travel Notes: {dest['travel_notes']}\n"
            f"---\n"
        )

    system_instruction = f"""
    You are a professional travel concierge for 'Lakbay', a premium Philippine travel application.
    Your task is to analyze the user's travel request and select the top 5 matching destinations from the database candidates provided below.

    You must perform a detailed matching evaluation for each candidate against the user request:
    1. Budget Range & Pricing Comparison:
       - Estimate the total cost of the trip based on:
         * Days of stay and number of travelers (extract these from the user's prompt).
         * Entrance fees (e.g., standard price per person or free).
         * Accommodation room prices (e.g., choose camping, budget huts, standard rooms, or luxury cabins based on user's budget class).
         * Selected or base activity prices.
       - Compare this calculated total against the user's total budget. If it significantly exceeds their budget, penalize or exclude it. If they have a premium/luxury budget, rank premium/luxury options higher. If they have a tight budget, rank free or budget-friendly options higher.
    2. Vibes, Categories, & Activities:
       - Match the desired vibes (relaxation, adventure, beach, surfing, sightseeing, hiking, shopping, history, food) to the destination's category, vibe tags, and specific available activities.
    3. Accessibility & Companions:
       - Check if the user is traveling with family, kids/children, pets, elderly/seniors, or has physical/wheelchair disabilities. Cross-reference these with the accessibility boolean flags. Rank accessible places higher if requested.

    Return EXACTLY 5 recommended items. If there are fewer than 5 candidates in the database, return all available candidates ranked.
    For each, return:
    - destination_id: The exact integer ID from the candidate.
    - score: A float between 0.0 and 100.0 indicating how perfectly it matches their prompt.
    - match_reason: A highly personalized, detailed 1-2 sentence description explaining exactly why this fits their budget (including entrance fees, activities, and accommodations), vibes, and companions/accessibility requirements.

    User Travel Request:
    "{prompt}"

    Database Candidates:
    {candidates_str}
    """

    response = model.generate_content(
        system_instruction,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": list[RecommendationItem]
        }
    )

    try:
        return json.loads(response.text)
    except Exception as e:
        # If parsing fails, throw error for standard fallback processing in router
        raise ValueError(f"Failed to parse Gemini structured JSON: {e}")