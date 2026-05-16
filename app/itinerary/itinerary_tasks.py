from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection

router = APIRouter(prefix="/itinerary-tasks", tags=["Itinerary Tasks"])


class ItineraryTaskCreate(BaseModel):
    day_id: int
    title: str
    assignee_id: int
    time_hint: str = ""
    notes: str = ""


@router.post("/")
def create_task(task: ItineraryTaskCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO itinerary_tasks
        (day_id, title, assignee_id, time_hint, notes)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        task.day_id,
        task.title,
        task.assignee_id,
        task.time_hint,
        task.notes
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Task created successfully"}


@router.get("/{day_id}")
def get_tasks(day_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM itinerary_tasks
        WHERE day_id = %s
    """, (day_id,))

    tasks = cur.fetchall()

    cur.close()
    conn.close()

    return {"tasks": tasks}


@router.put("/{task_id}")
def update_task(task_id: int, task: ItineraryTaskCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE itinerary_tasks
        SET title=%s,
            assignee_id=%s,
            time_hint=%s,
            notes=%s
        WHERE task_id=%s
    """, (
        task.title,
        task.assignee_id,
        task.time_hint,
        task.notes,
        task_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Task updated successfully"}


@router.delete("/{task_id}")
def delete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM itinerary_tasks
        WHERE task_id = %s
    """, (task_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Task deleted successfully"}