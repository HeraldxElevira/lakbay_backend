from fastapi import APIRouter
from app.auth.register import router as register_router
from app.auth.login import router as login_router

router = APIRouter(prefix="/auth", tags=["Users"])

router.include_router(register_router)
router.include_router(login_router)
