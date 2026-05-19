from fastapi import APIRouter, Header, HTTPException, status
from app.auth.register import router as register_router
from app.auth.login import router as login_router
from app.auth.jwt_handler import verify_token
from app.database.db import get_connection

router = APIRouter(prefix="/auth", tags=["Users"])

router.include_router(register_router)
router.include_router(login_router)

@router.get("/me", status_code=status.HTTP_200_OK)
def get_me(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information"
        )
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_id, email, name
            FROM users
            WHERE email = %s
        """, (email.strip().lower(),))
        
        result = cur.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        user_id, db_email, name = result
        return {
            "user_id": user_id,
            "email": db_email,
            "name": name if name else "Juan Dela Cruz"
        }
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

from pydantic import BaseModel

class ProfileUpdate(BaseModel):
    name: str = None

@router.put("/me", status_code=status.HTTP_200_OK)
def update_me(profile: ProfileUpdate, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information"
        )
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        name = profile.name.strip() if profile.name else None
        
        cur.execute("""
            UPDATE users
            SET name = %s
            WHERE email = %s
        """, (name, email.strip().lower()))
        
        conn.commit()
        return {"message": "Profile updated successfully"}
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
