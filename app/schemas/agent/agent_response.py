import uuid

from pydantic import BaseModel, Field

from app.schemas.itinerary.itinerary_request import Itinerary


class ItineraryEvaluation(BaseModel):
    valid_format: bool = Field(description="The itinerary matches the expected schema.")
    complete: bool = Field(
        description="Every trip day is covered, with correct dates and activities."
    )
    relevant: bool = Field(
        description="It mentions the destination and reflects the traveller's request."
    )
    score: float = Field(ge=0, le=1, description="Share of the three checks that passed.")
    problems: list[str] = Field(default_factory=list)


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
        description="Review problems left after the revision budget ran out. An itinerary with issues is never saved.",
    )
    saved: bool = Field(description="Whether the itinerary was written to the database.")
    error: str | None = None
    evaluation: ItineraryEvaluation | None = Field(
        default=None, description="Automatic quality checks on the generated itinerary."
    )
