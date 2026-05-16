from typing import List
import uuid
from pydantic import BaseModel, ConfigDict, Field


class Activity(BaseModel):
    title: str = Field(min_length=2, max_length=200)


class ItineraryDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day_number: int = Field(gt=0, le=1000)
    activities: List[Activity] = []


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: uuid.UUID
    day_number: int = Field(gt=0, le=1000)
    activities: List[Activity] = []


#  "itinerary_days": [
#       {
#         "trip_id": "19fc7eeb-a66a-41d8-a124-033e6af25756",
#         "day_number": 1,
#         "id": "aea5a985-58e2-43bc-a1df-0917530aabe5",
#         "activities": [
#           {
#             "itinerary_day_id": "aea5a985-58e2-43bc-a1df-0917530aabe5",
#             "title": "Hiking volcanoes",
#             "id": "69286ec2-274b-4403-afd5-91667db5bdc7"
#           }
#         ]
#       }
#     ]
