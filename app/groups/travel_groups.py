from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection

router = APIRouter(prefix="/travel-groups", tags=["Travel Groups"])


class TravelGroupCreate(BaseModel):
    name: str
    leader_id: int


@router.post("/")
def create_group(group: TravelGroupCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO travel_groups (name, leader_id)
        VALUES (%s, %s)
        RETURNING group_id
    """, (
        group.name,
        group.leader_id
    ))

    group_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Travel group created successfully",
        "group_id": group_id
    }


@router.get("/")
def get_all_groups():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM travel_groups")
    groups = cur.fetchall()

    cur.close()
    conn.close()

    return {"groups": groups}


@router.get("/{group_id}")
def get_group(group_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM travel_groups
        WHERE group_id = %s
    """, (group_id,))

    group = cur.fetchone()

    cur.close()
    conn.close()

    return {"group": group}


@router.delete("/{group_id}")
def delete_group(group_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM travel_groups
        WHERE group_id = %s
    """, (group_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Travel group deleted successfully"}