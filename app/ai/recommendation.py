from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.database.db import get_connection
from app.auth.dependencies import get_current_user

router = APIRouter()


class RecommendationRequest(BaseModel):
    prompt: str


@router.post("/ai/recommend", status_code=status.HTTP_200_OK)
def recommend(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM destinations")
        rows = cur.fetchall()

        results = []
        user_prompt = request.prompt.lower()

        for r in rows:
            score = 0

            name = r[1]
            description = r[2]
            lat = r[3]
            lng = r[4]
            cost = r[5]
            vibes = r[6].lower()
            rating = r[7]

            # vibe matching
            if "beach" in user_prompt and "beach" in vibes:
                score += 10

            if "nature" in user_prompt and "nature" in vibes:
                score += 10

            if "adventure" in user_prompt and "adventure" in vibes:
                score += 10

            if "relax" in user_prompt and "relax" in vibes:
                score += 10

            # budget
            if cost <= 50000:
                score += 5

            # rating boost
            score += rating

            results.append({
                "id": r[0],
                "name": name,
                "description": description,
                "lat": lat,
                "lng": lng,
                "cost": cost,
                "vibes": vibes,
                "rating": rating,
                "score": score
            })

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return {
            "message": "AI recommendations generated",
            "requested_by": current_user["email"],
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