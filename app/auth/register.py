from fastapi import APIRouter
from pydantic import BaseModel
from app.database.db import get_connection
from app.utils.security import hash_password

router = APIRouter()

class User(BaseModel):
    email: str
    password: str
    name: str = None


@router.post("/register")
def register(user: User):
    conn = get_connection()
    cur = conn.cursor()

    email = user.email.strip().lower()
    hashed_pw = hash_password(user.password)
    name = user.name.strip() if user.name else None

    cur.execute(
        "INSERT INTO users (email, password, name) VALUES (%s, %s, %s)",
        (email, hashed_pw, name)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Registered successfully"}