from app.agents.evaluation import evaluate_itinerary
from tests.helpers import TRIP, make_days


def test_a_good_itinerary_scores_full_marks():
    result = evaluate_itinerary(TRIP, make_days(), "museums and food")

    assert result.model_dump() == {
        "valid_format": True,
        "complete": True,
        "relevant": True,
        "score": 1.0,
        "problems": [],
    }


def test_a_request_is_optional():
    assert evaluate_itinerary(TRIP, make_days()).score == 1.0


def test_an_incomplete_itinerary_loses_the_completeness_mark():
    result = evaluate_itinerary(TRIP, make_days(2))

    assert result.complete is False
    assert result.score == 0.67
    assert result.problems


def test_an_itinerary_for_another_place_is_not_relevant():
    trip = {**TRIP, "destination": "Kigali, Rwanda"}

    result = evaluate_itinerary(trip, make_days())

    assert result.relevant is False
    assert "never mentions Kigali, Rwanda" in result.problems[0]


def test_an_ignored_request_is_not_relevant():
    result = evaluate_itinerary(TRIP, make_days(), "snowboarding and skiing")

    assert result.relevant is False
    assert result.score == 0.67


def test_a_malformed_itinerary_fails_every_check():
    result = evaluate_itinerary(TRIP, [{"day": "first"}])

    assert (result.valid_format, result.complete, result.relevant) == (False, False, False)
    assert result.score == 0.0


def test_an_empty_itinerary_passes_format_only():
    result = evaluate_itinerary(TRIP, [])

    assert (result.valid_format, result.complete, result.relevant) == (True, False, False)
    assert result.score == 0.33
