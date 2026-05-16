from fastapi import APIRouter
from app.trips.trips import router as trips_router
from app.trips.trip_locations import router as trip_locations_router
from app.trips.expenses import router as expenses_router

router = APIRouter(prefix="/trips", tags=["Trips"])

router.include_router(trips_router)
router.include_router(trip_locations_router)
router.include_router(expenses_router)