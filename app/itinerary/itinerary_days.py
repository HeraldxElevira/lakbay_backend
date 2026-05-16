from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection

router = APIRouter(prefix="/itinerary-days", tags=["Itinerary Days"])


class ItineraryDayCreate(BaseModel):
    trip_id: int
    day_number: int
    location_id: int
    notes: str = ""


@router.post("/")
def create_itinerary_day(day: ItineraryDayCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO itinerary_days
        (trip_id, day_number, location_id, notes)
        VALUES (%s, %s, %s, %s)
    """, (
        day.trip_id,
        day.day_number,
        day.location_id,
        day.notes
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Itinerary day created successfully"}


@router.get("/{trip_id}")
def get_itinerary_days(trip_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM itinerary_days
        WHERE trip_id = %s
        ORDER BY day_number
    """, (trip_id,))

    days = cur.fetchall()

    cur.close()
    conn.close()

    return {"days": days}


@router.put("/{day_id}")
def update_itinerary_day(day_id: int, day: ItineraryDayCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE itinerary_days
        SET day_number=%s,
            location_id=%s,
            notes=%s
        WHERE day_id=%s
    """, (
        day.day_number,
        day.location_id,
        day.notes,
        day_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Itinerary day updated successfully"}


@router.delete("/{day_id}")
def delete_itinerary_day(day_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM itinerary_days
        WHERE day_id = %s
    """, (day_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Itinerary day deleted successfully"}