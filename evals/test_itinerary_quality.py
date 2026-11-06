"""DeepEval quality checks on itineraries from the real workflow.

These call Claude and the live travel tools, so they cost tokens:

    uv run deepeval test run evals/
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from app.agents.evaluation import evaluate_itinerary
from evals.conftest import DATASET
from evals.judge import ClaudeJudge

judge = ClaudeJudge()


def _render(days: list[dict]) -> str:
    lines = []
    for day in days:
        lines.append(f"Day {day['day']} ({day.get('date')}): {day.get('title') or ''}")
        for activity in day.get("activities") or []:
            place = (activity.get("location") or {}).get("name") or ""
            lines.append(
                f"- {activity.get('start_time') or ''} {activity['title']}, {place}: "
                f"{activity.get('description') or ''}"
            )
    return "\n".join(lines)


def _request(case: dict) -> str:
    trip = case["trip"]
    return (
        f"Plan a {trip['days']}-day trip to {trip['destination']} from {trip['start_date']} "
        f"to {trip['end_date']} on a budget of {trip['budget']} USD. {case['user_request']}"
    )


@pytest.mark.parametrize("case", DATASET["itineraries"], ids=lambda case: case["name"])
def test_itinerary_quality(case, live_results):
    result = live_results[0][case["name"]]
    assert result["error"] is None
    assert result["issues"] == []

    assert_test(
        LLMTestCase(
            input=_request(case),
            actual_output=_render(result["itinerary"]),
            expected_output=case["expected_output"],
            retrieval_context=[result["research"]],
        ),
        [
            AnswerRelevancyMetric(threshold=0.7, model=judge),
            FaithfulnessMetric(threshold=0.7, model=judge),
            GEval(
                name="Completeness",
                criteria=(
                    "The actual output covers every requested day and date, gives each day "
                    "concrete activities, and meets the plan described in the expected output."
                ),
                evaluation_params=[
                    SingleTurnParams.INPUT,
                    SingleTurnParams.ACTUAL_OUTPUT,
                    SingleTurnParams.EXPECTED_OUTPUT,
                ],
                threshold=0.7,
                model=judge,
            ),
        ],
    )


@pytest.mark.parametrize("case", DATASET["itineraries"], ids=lambda case: case["name"])
def test_itinerary_passes_the_built_in_checks(case, live_results):
    result = live_results[0][case["name"]]

    evaluation = evaluate_itinerary(case["trip"], result["itinerary"], case["user_request"])

    assert evaluation.problems == []
    assert evaluation.score == 1.0
