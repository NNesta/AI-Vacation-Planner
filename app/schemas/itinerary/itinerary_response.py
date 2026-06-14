from typing import List
import uuid
from pydantic import BaseModel, ConfigDict, Field


class Activity(BaseModel):
    title: str = Field(min_length=2, max_length=200)


class Itinerary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: int = Field(gt=0, le=1000)
    activities: List[Activity] = []


class ItineraryCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: uuid.UUID
    itineraries: List[Itinerary]
    message: str = "Itinerary created successfully"


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: uuid.UUID
    itineraries: List[Itinerary]
