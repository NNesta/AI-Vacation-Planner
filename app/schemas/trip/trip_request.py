from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.enums.trip_budget_enum import TripStyle


class UpdateTripRequest(BaseModel):
    destination: Optional[str] = Field(min_length=2, max_length=200, default=None)
    budget: Optional[Decimal] = Field(
        ge=0, le=1_000_000, decimal_places=2, default=None
    )
    trip_style: Optional[TripStyle] = None
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")

        if self.start_datetime <= datetime.now(timezone.utc):
            raise ValueError("start_datetime must be in the future")

        return self


class CreateTripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=200)
    budget: Decimal = Field(
        default=Decimal("1.00"), ge=0, le=1_000_000, decimal_places=2
    )
    trip_style: TripStyle = Field(default=TripStyle.BUDGET)
    start_datetime: datetime
    end_datetime: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")

        if self.start_datetime <= datetime.now(timezone.utc):
            raise ValueError("start_datetime must be in the future")

        return self
