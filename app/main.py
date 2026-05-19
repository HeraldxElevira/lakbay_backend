from fastapi import FastAPI
from app.auth.router import router as auth_router
from app.ai.router import router as ai_router   
from app.trips.router import router as trips_router
from app.trips.trip_locations import router as trip_locations_router
from app.trips.expenses import router as expenses_router
from app.groups.group_members import router as group_members_router
from app.groups.travel_groups import router as travel_groups_router
from app.itinerary.itinerary_days import router as itinerary_days_router
from app.itinerary.itinerary_tasks import router as itinerary_tasks_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Lakbay+ Backend",)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(trips_router)
app.include_router(trip_locations_router)
app.include_router(expenses_router)
app.include_router(group_members_router)
app.include_router(travel_groups_router)
app.include_router(itinerary_days_router)
app.include_router(itinerary_tasks_router)

@app.get("/", tags=["Root"])
def home():
    return {"message": "Lakbay+ Backend Running"}