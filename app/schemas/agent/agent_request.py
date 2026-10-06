import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="What the traveller wants, in plain language.",
        examples=["Plan my Paris trip and include weather-friendly activities."],
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation id returned by a previous call. Omit to start a new conversation.",
    )
    trip_id: uuid.UUID | None = Field(
        default=None,
        description="Optional trip the question is about; lets the agent look up its dates and budget.",
    )


class GenerateItineraryRequest(BaseModel):
    user_request: str | None = Field(
        default=None,
        max_length=2000,
        description="Extra instructions for this itinerary, e.g. 'keep it weather-friendly and low-cost'.",
    )
    save: bool = Field(
        default=True,
        description="Whether to replace the trip's stored itinerary with the generated one.",
    )
