import uuid
from datetime import time

from pydantic import BaseModel, Field, ValidationError


class Location(BaseModel):
    name: str = Field(
        description="Name of the specific place, attraction, restaurant, hotel, park, or destination."
    )

    address: str | None = Field(
        default=None,
        description="Physical address or location details that help travelers find the place.",
    )


class Activity(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=200,
        description="Short, clear name describing the activity, experience, or destination.",
    )

    description: str | None = Field(
        default=None,
        description="Concise explanation of what travelers will do, see, or experience.",
    )

    start_time: time | None = Field(
        default=None,
        description="Recommended time when travelers should start the activity.",
    )

    end_time: time | None = Field(
        default=None,
        description="Recommended time when travelers should finish the activity.",
    )

    duration_minutes: int | None = Field(
        default=None,
        gt=0,
        description="Estimated time in minutes needed to complete or enjoy the activity.",
    )

    location: Location | None = Field(
        default=None, description="Specific place where the activity takes place."
    )

    tips: list[str] = Field(
        default_factory=list,
        description="Practical recommendations for improving the traveler's experience.",
    )


class Itinerary(BaseModel):
    day: int = Field(
        gt=0, le=1000, description="Sequential day number within the trip itinerary."
    )

    date: str | None = Field(
        default=None,
        description="Calendar date for this itinerary day, preferably using YYYY-MM-DD format.",
    )

    title: str | None = Field(
        default=None,
        description="Short title summarizing the main theme or focus of the day.",
    )

    summary: str | None = Field(
        default=None,
        description="Concise overview of the day's main experiences and destinations.",
    )

    activities: list[Activity] = Field(
        default_factory=list,
        description="Ordered list of activities planned for this day.",
    )


class LLMItineraryResponse(BaseModel):
    itineraries: list[Itinerary] = Field(
        default_factory=list,
        description="Complete list of day-by-day itineraries to create for the trip.",
    )


class CreateItineraryRequest(BaseModel):
    trip_id: uuid.UUID = Field(
        description="Unique identifier of the trip associated with this itinerary."
    )

    itineraries: list[Itinerary] = Field(
        default_factory=list,
        description="Complete list of day-by-day itineraries to create for the trip.",
    )


def validate_with_model(data_model, llm_response):
    try:
        validated_data = data_model.model_validate_json(llm_response)
        print("Data were validated successfully")
        print(validated_data.model_dump_json(indent=2))
        return validated_data, None
    except ValidationError as e:
        print(f"Error Validating data: {e}")
        error_message = f"This response generated a validation error: {e}"
        return None, error_message
