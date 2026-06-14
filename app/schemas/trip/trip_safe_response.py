from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from app.models.trip import TripStyle


class TripSafeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(max_length=250)
    destination: str = Field(min_length=2, max_length=200)
    days: int = Field(default=1, ge=0, le=50)
    budget: Decimal = Field(
        default=Decimal("1.00"), ge=0, le=1_000_000, decimal_places=2
    )
    trip_style: TripStyle = Field(default=TripStyle.BUDGET)
    start_datetime: datetime
    end_datetime: datetime


class CreateTripResponse(TripSafeResponse):
    message: str = Field(default="Trip created successfully", max_length=100)
