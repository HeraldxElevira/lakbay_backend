from fastapi import APIRouter
from app.ai.recommendation import router as recommendation_router

router = APIRouter(prefix="/ai-recommendation", tags=["AI Recommendation"])

router.include_router(recommendation_router)