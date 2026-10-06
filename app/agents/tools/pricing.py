"""Pricing tool — heuristic on-the-ground cost estimates.

There is no free, keyless API that returns real hotel/flight prices, so this
tool is an explicit model rather than a lookup: per-destination daily baselines
scaled by travel style. Every response says so, so the agent presents the
numbers as estimates and never as quoted prices.
"""

from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Mid-range daily cost per traveller, in USD, covering lodging + food + local
# transport + activities. Sourced from published backpacker/mid-range budget
# guides; good enough to sanity-check a plan, not to book against.
DAILY_BASELINES_USD: dict[str, float] = {
    "rwanda": 85,
    "kigali": 85,
    "uganda": 75,
    "kenya": 95,
    "tanzania": 100,
    "ethiopia": 60,
    "morocco": 70,
    "egypt": 65,
    "south africa": 90,
    "france": 180,
    "paris": 200,
    "italy": 165,
    "rome": 170,
    "spain": 140,
    "portugal": 120,
    "united kingdom": 195,
    "london": 215,
    "germany": 155,
    "netherlands": 175,
    "switzerland": 260,
    "greece": 130,
    "turkey": 80,
    "united states": 210,
    "new york": 270,
    "canada": 175,
    "mexico": 85,
    "brazil": 85,
    "argentina": 75,
    "peru": 70,
    "japan": 165,
    "tokyo": 185,
    "china": 105,
    "thailand": 65,
    "vietnam": 50,
    "indonesia": 60,
    "bali": 70,
    "india": 45,
    "nepal": 45,
    "united arab emirates": 190,
    "dubai": 200,
    "australia": 185,
    "new zealand": 170,
}
DEFAULT_DAILY_USD = 110.0

# Multipliers applied to the baseline. BUDGET matches the trip_style enum.
STYLE_MULTIPLIERS: dict[str, float] = {
    "budget": 0.55,
    "backpacker": 0.45,
    "standard": 1.0,
    "comfort": 1.0,
    "mid-range": 1.0,
    "family": 1.15,
    "adventure": 1.1,
    "luxury": 2.4,
    "premium": 2.0,
}
DEFAULT_MULTIPLIER = 1.0

# How a day's spend splits across categories.
CATEGORY_SHARES: dict[str, float] = {
    "accommodation": 0.42,
    "food_and_drink": 0.25,
    "local_transport": 0.12,
    "activities_and_entry_fees": 0.21,
}


class PricingInput(BaseModel):
    destination: str = Field(description="Where the trip takes place, e.g. 'Kigali'.")
    days: int = Field(ge=1, le=120, description="Number of days on the ground.")
    travelers: int = Field(default=1, ge=1, le=20, description="How many people travel.")
    trip_style: str = Field(
        default="standard",
        description="Travel style, e.g. 'budget', 'standard', 'luxury', 'family'.",
    )
    budget: float | None = Field(
        default=None,
        description="The traveller's total budget in USD, if known, to check feasibility.",
    )


def _baseline_for(destination: str) -> tuple[float, bool]:
    """Look up a daily baseline; returns the value and whether it was a real match."""
    needle = destination.strip().lower()
    if needle in DAILY_BASELINES_USD:
        return DAILY_BASELINES_USD[needle], True
    for key, value in DAILY_BASELINES_USD.items():
        if key in needle or needle in key:
            return value, True
    return DEFAULT_DAILY_USD, False


@tool("estimate_trip_cost", args_schema=PricingInput)
async def estimate_trip_cost(
    destination: str,
    days: int,
    travelers: int = 1,
    trip_style: str = "standard",
    budget: float | None = None,
) -> dict:
    """Estimate what a trip will cost on the ground, broken down by category.

    Use this when the user asks about cost or affordability, and whenever you
    are building an itinerary against a stated budget — call it before
    committing to a plan so you can adjust the activity mix if the plan does not
    fit.

    Pass the user's total budget to get a feasibility verdict and a per-day
    spending allowance to design against.

    These are modelled estimates from published daily-budget ranges, not live
    prices, and they exclude international flights and visas. Always present
    them as estimates.
    """
    daily_base, matched = _baseline_for(destination)
    multiplier = STYLE_MULTIPLIERS.get(trip_style.strip().lower(), DEFAULT_MULTIPLIER)
    daily_per_person = daily_base * multiplier
    total = daily_per_person * days * travelers

    breakdown = {
        category: round(total * share, 2)
        for category, share in CATEGORY_SHARES.items()
    }

    result = {
        "destination": destination,
        "days": days,
        "travelers": travelers,
        "trip_style": trip_style,
        "currency": "USD",
        "estimated_daily_cost_per_person": round(daily_per_person, 2),
        "estimated_total": round(total, 2),
        "breakdown": breakdown,
        "excludes": ["international flights", "visas", "travel insurance"],
        "confidence": (
            "medium — destination matched a known cost baseline"
            if matched
            else "low — no cost baseline for this destination, used a global average"
        ),
        "disclaimer": "Modelled estimate from published daily-budget ranges, not a live price quote.",
    }

    if budget is not None:
        headroom = budget - total
        result["budget_check"] = {
            "budget": round(budget, 2),
            "difference": round(headroom, 2),
            "fits": headroom >= 0,
            "daily_allowance_per_person": round(budget / days / travelers, 2),
            "verdict": (
                f"Comfortable — about ${headroom:,.0f} of headroom."
                if headroom >= total * 0.15
                else "Tight but workable — keep paid activities modest."
                if headroom >= 0
                else f"Over budget by about ${abs(headroom):,.0f} — "
                "cut paid activities, shorten the trip, or choose cheaper lodging."
            ),
        }

    return result
