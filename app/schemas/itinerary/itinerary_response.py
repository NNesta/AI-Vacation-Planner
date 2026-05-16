from typing import List
import uuid
from pydantic import BaseModel, ConfigDict, Field


class Activity(BaseModel):
    title: str = Field(min_length=2, max_length=200)


class ItineraryDay(BaseModel):
    day: str = Field(gt=0, le=1000)
    activities: List[Activity] = []


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: uuid.UUID
    itineraries: List[ItineraryDay] = []
    message: str
