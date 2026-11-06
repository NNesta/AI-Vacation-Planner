import pytest
from pydantic import ValidationError

from app.agents.itinerary_graph import review_itinerary
from app.schemas.itinerary.itinerary_request import (
    LLMItineraryResponse,
    validate_with_model,
)
from tests.helpers import TRIP, make_days


def test_a_complete_itinerary_validates():
    parsed = LLMItineraryResponse.model_validate({"itineraries": make_days()})

    assert len(parsed.itineraries) == 3
    assert parsed.itineraries[0].activities[0].location.name == "Louvre"


@pytest.mark.parametrize(
    "mutation",
    [
        {"day": 0},
        {"day": "first"},
        {"activities": [{"title": "x"}]},
        {"activities": [{"description": "no title"}]},
        {"activities": [{"title": "Louvre", "duration_minutes": 0}]},
        {"activities": [{"title": "Louvre", "start_time": "not-a-time"}]},
        {"activities": "Louvre"},
    ],
)
def test_malformed_days_are_rejected(mutation):
    with pytest.raises(ValidationError):
        LLMItineraryResponse.model_validate({"itineraries": [{**make_days(1)[0], **mutation}]})


def test_validate_with_model_returns_data_for_valid_json():
    data, error = validate_with_model(LLMItineraryResponse, '{"itineraries": []}')

    assert error is None
    assert data.itineraries == []


def test_validate_with_model_returns_an_error_for_invalid_json():
    data, error = validate_with_model(LLMItineraryResponse, "not json")

    assert data is None
    assert "validation error" in error


def test_review_accepts_a_correct_itinerary():
    assert review_itinerary(TRIP, make_days()) == []


def test_review_rejects_an_empty_itinerary():
    assert "empty" in review_itinerary(TRIP, [])[0]


def test_review_rejects_the_wrong_number_of_days():
    assert any("exactly 3" in issue for issue in review_itinerary(TRIP, make_days(2)))


def test_review_rejects_wrong_dates():
    days = make_days(start="2031-01-01")

    assert any("should be 2030-05-10" in issue for issue in review_itinerary(TRIP, days))


def test_review_rejects_out_of_order_day_numbers():
    days = make_days()
    days[0]["day"], days[1]["day"] = 2, 1

    assert any("Day numbers" in issue for issue in review_itinerary(TRIP, days))


def test_review_rejects_a_day_without_activities():
    days = make_days()
    days[1]["activities"] = []

    assert any("no activities" in issue for issue in review_itinerary(TRIP, days))


def test_review_rejects_too_many_activities():
    days = make_days()
    days[0]["activities"] = days[0]["activities"] * 7

    assert any("at most 6" in issue for issue in review_itinerary(TRIP, days))


def test_review_rejects_an_activity_ending_before_it_starts():
    days = make_days()
    days[0]["activities"][0]["end_time"] = "09:00:00"

    assert any("ends at or before" in issue for issue in review_itinerary(TRIP, days))
