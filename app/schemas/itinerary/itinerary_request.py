from typing import List
import uuid
from pydantic import BaseModel, Field


class Activity(BaseModel):
    title: str = Field(min_length=2, max_length=200)


class ItineraryDay(BaseModel):
    day: int = Field(gt=0, le=1000)
    activities: List[Activity] = []


class CreateItineraryRequest(BaseModel):
    trip_id: uuid.UUID
    itinerary_days: List[ItineraryDay]
