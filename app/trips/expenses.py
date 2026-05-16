from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection

router = APIRouter(prefix="/expenses", tags=["Expenses"])


class ExpenseCreate(BaseModel):
    trip_id: int
    category: str
    amount: float
    assigned_to: int


@router.post("/")
def create_expense(expense: ExpenseCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses (trip_id, category, amount, assigned_to)
        VALUES (%s, %s, %s, %s)
    """, (
        expense.trip_id,
        expense.category,
        expense.amount,
        expense.assigned_to
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Expense added successfully"}


@router.get("/{trip_id}")
def get_expenses(trip_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM expenses
        WHERE trip_id = %s
    """, (trip_id,))

    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return {"expenses": expenses}


@router.put("/{expense_id}")
def update_expense(expense_id: int, expense: ExpenseCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE expenses
        SET category=%s, amount=%s, assigned_to=%s
        WHERE expense_id=%s
    """, (
        expense.category,
        expense.amount,
        expense.assigned_to,
        expense_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Expense updated successfully"}


@router.delete("/{expense_id}")
def delete_expense(expense_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM expenses
        WHERE expense_id = %s
    """, (expense_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Expense deleted successfully"}