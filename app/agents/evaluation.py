"""Deterministic quality checks for a generated itinerary."""

from __future__ import annotations

import re

from pydantic import ValidationError

from app.agents.itinerary_graph import review_itinerary
from app.schemas.agent import ItineraryEvaluation
from app.schemas.itinerary.itinerary_request import LLMItineraryResponse

STOPWORDS = frozenset(
    "the and for with from that this these those are was were you your our can could "
    "should would will please want need like make keep give some any all not new "
    "trip plan day days itinerary".split()
)


def _keywords(text: str) -> set[str]:
    return {word for word in re.findall(r"[^\W\d_]{3,}", text.lower()) if word not in STOPWORDS}


def _itinerary_text(days: list[dict]) -> str:
    parts: list[str | None] = []
    for day in days:
        parts += [day.get("title"), day.get("summary")]
        for activity in day.get("activities") or []:
            location = activity.get("location") or {}
            parts += [
                activity.get("title"),
                activity.get("description"),
                location.get("name"),
                location.get("address"),
                *(activity.get("tips") or []),
            ]
    return " ".join(part for part in parts if part)


def _relevance_problems(trip: dict, days: list[dict], user_request: str | None) -> list[str]:
    covered = _keywords(_itinerary_text(days))
    problems = []
    if not _keywords(trip["destination"]) & covered:
        problems.append(f"The itinerary never mentions {trip['destination']}.")
    requested = _keywords(user_request or "")
    if requested and not requested & covered:
        problems.append("The itinerary does not reflect the traveller's request.")
    return problems


def evaluate_itinerary(
    trip: dict, days: list[dict], user_request: str | None = None
) -> ItineraryEvaluation:
    try:
        LLMItineraryResponse.model_validate({"itineraries": days})
    except ValidationError as exc:
        return ItineraryEvaluation(
            valid_format=False,
            complete=False,
            relevant=False,
            score=0.0,
            problems=[error["msg"] for error in exc.errors()],
        )

    review_problems = review_itinerary(trip, days)
    relevance_problems = _relevance_problems(trip, days, user_request) if days else []
    complete = not review_problems
    relevant = bool(days) and not relevance_problems
    return ItineraryEvaluation(
        valid_format=True,
        complete=complete,
        relevant=relevant,
        score=round((1 + complete + relevant) / 3, 2),
        problems=[*review_problems, *relevance_problems],
    )
