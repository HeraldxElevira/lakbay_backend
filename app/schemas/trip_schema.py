from pydantic import BaseModel
from typing import Optional


class TripCreate(BaseModel):
    group_id: int
    title: str
    start_date: str
    end_date: str
    total_budget: float
    created_by: int


class TripUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_budget: Optional[float] = None