from fastapi import APIRouter
from app.itinerary.itinerary_days import router as itinerary_days_router
from app.itinerary.itinerary_tasks import router as itinerary_tasks_router

router = APIRouter(prefix="/itinerary-days", tags=["Itinerary Days"])

router.include_router(itinerary_days_router)
router.include_router(itinerary_tasks_router)