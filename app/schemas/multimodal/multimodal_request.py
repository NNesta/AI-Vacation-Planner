from datetime import date

from pydantic import BaseModel, Field


class SpokenTripDetails(BaseModel):
    title: str = Field(
        description="Short, friendly title for the trip, e.g. 'Lisbon food weekend'."
    )
    description: str = Field(
        description="One sentence on what the traveller wants from the trip: interests, pace, who is going."
    )
    destination: str | None = Field(
        default=None,
        description="City, region or country to visit. Null if the traveller did not say.",
    )
    start_date: date | None = Field(
        default=None,
        description="First day of the trip as YYYY-MM-DD. Null if the traveller did not say.",
    )
    end_date: date | None = Field(
        default=None,
        description="Last day of the trip as YYYY-MM-DD. Null if neither an end date nor a trip length was said.",
    )
    budget: float | None = Field(
        default=None,
        description="Total trip budget in US dollars. Null if no amount was said.",
    )
