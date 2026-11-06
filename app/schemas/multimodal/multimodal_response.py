from pydantic import BaseModel, Field

from app.schemas.trip.trip_safe_response import CreateTripResponse


class VoiceTripResponse(BaseModel):
    transcript: str = Field(description="What the speech-to-text model heard.")
    trip: CreateTripResponse
