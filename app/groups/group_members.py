from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.database.db import get_connection

router = APIRouter(prefix="/group-members", tags=["Group Members"])


class AddMembers(BaseModel):
    group_id: int
    user_ids: List[int]


@router.post("/")
def add_members(data: AddMembers):
    conn = get_connection()
    cur = conn.cursor()

    for user_id in data.user_ids:
        cur.execute("""
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (%s, %s, %s)
        """, (
            data.group_id,
            user_id,
            "member"
        ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Members added successfully"}


@router.get("/{group_id}")
def get_group_members(group_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM group_members
        WHERE group_id = %s
    """, (group_id,))

    members = cur.fetchall()

    cur.close()
    conn.close()

    return {"members": members}


@router.delete("/{group_id}/{user_id}")
def remove_member(group_id: int, user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM group_members
        WHERE group_id = %s AND user_id = %s
    """, (group_id, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Member removed successfully"}