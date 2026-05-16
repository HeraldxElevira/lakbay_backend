from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.database.db import get_connection

router = APIRouter(prefix="/trip-locations", tags=["Trip Locations"])


class TripLocationCreate(BaseModel):
    trip_id: int
    destination_ids: List[int]


@router.post("/")
def add_trip_locations(data: TripLocationCreate):
    conn = get_connection()
    cur = conn.cursor()

    for destination_id in data.destination_ids:
        cur.execute("""
            INSERT INTO trip_locations (trip_id, destination_id, is_selected)
            VALUES (%s, %s, %s)
        """, (
            data.trip_id,
            destination_id,
            True
        ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Trip locations added successfully"}


@router.get("/{trip_id}")
def get_trip_locations(trip_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM trip_locations
        WHERE trip_id = %s
    """, (trip_id,))

    locations = cur.fetchall()

    cur.close()
    conn.close()

    return {"locations": locations}


@router.delete("/{trip_id}/{destination_id}")
def remove_trip_location(trip_id: int, destination_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM trip_locations
        WHERE trip_id = %s AND destination_id = %s
    """, (
        trip_id,
        destination_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Trip location removed successfully"}