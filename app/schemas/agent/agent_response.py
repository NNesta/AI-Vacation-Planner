import uuid

from pydantic import BaseModel, Field

from app.schemas.itinerary.itinerary_request import Itinerary


class ChatResponse(BaseModel):
    thread_id: str = Field(description="Pass this back to continue the conversation.")
    answer: str
    tools_used: list[str] = Field(
        default_factory=list,
        description="Tools the agent chose to call for this turn, in order.",
    )


class GeneratedItineraryResponse(BaseModel):
    trip_id: uuid.UUID
    itinerary: list[Itinerary] = Field(default_factory=list)
    tools_used: list[str] = Field(
        default_factory=list, description="Tools the research agent called."
    )
    research: str | None = Field(
        default=None, description="The research brief the itinerary was written from."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Review problems still outstanding after the revision budget ran out.",
    )
    saved: bool = Field(description="Whether the itinerary was written to the database.")
    error: str | None = None
