from typing import List
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from app.enums.trip_budget_enum import TripStyle
from app.schemas.itinerary.itinerary_response import ItineraryDay
from app.schemas.user.user_safe_response import UserSafeResponse


class UserTripSchema(BaseModel):

    status: str
    user: UserSafeResponse
    model_config = {"from_attributes": True}


class TripResponse(BaseModel):
    id: UUID
    destination: str = Field(min_length=2, max_length=200)
    days: int = Field(default=1, ge=0, le=50)
    budget: Decimal = Field(
        default=Decimal("1.00"), ge=0, le=1_000_000, decimal_places=2
    )
    trip_style: TripStyle = Field(default=TripStyle.BUDGET)
    user_trips: List[UserTripSchema]
    creator: UserSafeResponse
    itinerary_days: List[ItineraryDay]
