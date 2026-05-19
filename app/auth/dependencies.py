from fastapi import Header, HTTPException, status
from app.auth.jwt_handler import verify_token


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    token = authorization.split(" ")[1]

    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload


def get_current_user_optional(authorization: str = Header(None)):
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        return payload
    except Exception:
        return None