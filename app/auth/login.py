from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.database.db import get_connection
from app.utils.security import verify_password
from app.auth.jwt_handler import create_access_token

router = APIRouter()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", status_code=status.HTTP_200_OK)
def login(user: UserLogin):
    try:
        conn = get_connection()
        cur = conn.cursor()

        email = user.email.strip().lower()

        cur.execute("""
            SELECT user_id, email, password, name
            FROM users
            WHERE email = %s
        """, (email,))

        result = cur.fetchone()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_id, db_email, hashed_password, name = result

        if not verify_password(user.password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )

        token = create_access_token({
            "user_id": user_id,
            "email": db_email
        })

        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "name": name if name else "Juan Dela Cruz",
            "email": db_email
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()