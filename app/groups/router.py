from fastapi import APIRouter
from app.groups.group_members import router as group_members_router
from app.groups.travel_groups import router as travel_groups_router

router = APIRouter(prefix="/group-members", tags=["Group Members"])

router.include_router(group_members_router)
router.include_router(travel_groups_router)