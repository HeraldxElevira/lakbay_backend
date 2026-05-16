from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection
from app.utils.security import hash_password

router = APIRouter()

class User(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(user: User):
    conn = get_connection()
    cur = conn.cursor()

    email = user.email.strip().lower()
    hashed_pw = hash_password(user.password)

    cur.execute(
        "INSERT INTO users (email, password) VALUES (%s, %s)",
        (email, hashed_pw)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Registered successfully"}