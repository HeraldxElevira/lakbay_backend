from fastapi import APIRouter
from app.database.db import get_connection
from app.schemas.trip_schema import TripCreate, TripUpdate
from fastapi import APIRouter, HTTPException
from psycopg2 import Error

router = APIRouter()
# =========================
# CREATE TRIP
# =========================

@router.post("/")
def create_trip(trip: TripCreate):
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO trips 
            (group_id, title, start_date, end_date, total_budget, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING trip_id
        """, (
            trip.group_id,
            trip.title,
            trip.start_date,
            trip.end_date,
            trip.total_budget,
            trip.created_by
        ))

        result = cur.fetchone()

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Trip creation failed: no trip ID returned"
            )

        trip_id = result[0]
        conn.commit()

        return {
            "message": "Trip created successfully",
            "trip_id": trip_id
        }

    except Error as db_error:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(db_error)}"
        )

    except Exception as e:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# =========================
# GET ALL TRIPS BY GROUP
# =========================
@router.get("/group/{group_id}")
def get_trips(group_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM trips WHERE group_id = %s
    """, (group_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "trips": rows
    }


# =========================
# GET SINGLE TRIP
# =========================
@router.get("/{trip_id}")
def get_trip(trip_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM trips WHERE trip_id = %s
    """, (trip_id,))

    trip = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "trip": trip
    }


# =========================
# UPDATE TRIP
# =========================
@router.put("/{trip_id}")
def update_trip(trip_id: int, trip: TripUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE trips
        SET title = COALESCE(%s, title),
            start_date = COALESCE(%s, start_date),
            end_date = COALESCE(%s, end_date),
            total_budget = COALESCE(%s, total_budget)
        WHERE trip_id = %s
    """, (
        trip.title,
        trip.start_date,
        trip.end_date,
        trip.total_budget,
        trip_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Trip updated"}


# =========================
# DELETE TRIP
# =========================
@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM trips WHERE trip_id = %s
    """, (trip_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Trip deleted"}