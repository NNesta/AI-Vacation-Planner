from uuid import UUID
from pydantic import ConfigDict, Field
from .trip_request import TripBase


class TripSafeResponse(TripBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class CreateTripResponse(TripSafeResponse):
    message: str = Field(default="Trip created successfully", max_length=100)
