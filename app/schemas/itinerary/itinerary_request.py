from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class Activity(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None


class Itinerary(BaseModel):
    day: int = Field(gt=0, le=1000)
    activities: List[Activity] = []


class CreateItineraryRequest(BaseModel):
    trip_id: uuid.UUID
    itineraries: List[Itinerary]
