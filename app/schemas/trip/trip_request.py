from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from app.enums.trip_budget_enum import TripStyle


class UpdateTripRequest(BaseModel):
    destination: Optional[str] = Field(min_length=2, max_length=200, default=None)
    days: Optional[int] = Field(ge=0, le=50, default=None)
    budget: Optional[Decimal] = Field(
        ge=0, le=1_000_000, decimal_places=2, default=None
    )
    trip_style: Optional[TripStyle] = None


class CreateTripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=200)
    days: int = Field(default=1, ge=0, le=50)
    budget: Decimal = Field(
        default=Decimal("1.00"), ge=0, le=1_000_000, decimal_places=2
    )
    trip_style: TripStyle = Field(default=TripStyle.BUDGET)
