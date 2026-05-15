from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

from app.models.trips import TripStyle


class TripSafeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    destination: str = Field(min_length=2, max_length=200)
    days: int = Field(default=1, ge=0, le=50)
    budget: Decimal = Field(
        default=Decimal("1.00"), ge=0, le=1_000_000, decimal_places=2
    )
    trip_style: TripStyle = Field(default=TripStyle.BUDGET)


class CreateTripResponse(TripSafeResponse):
    message: str = Field(default="Trip created successfully", max_length=100)
