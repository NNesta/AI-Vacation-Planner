import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

import pytest  # noqa: E402

from app.mcp.client import connect_mcp  # noqa: E402
from app.services import agent_services  # noqa: E402
from app.services.itinerary import generate_itineraries  # noqa: E402

DATASET = json.loads((Path(__file__).parent / "golden_dataset.json").read_text())


async def _load_golden_trip(trip_id: UUID) -> dict:
    return next(
        case["trip"] for case in DATASET["itineraries"] if case["trip"]["trip_id"] == str(trip_id)
    )


async def _run_workflows() -> tuple[dict, dict]:
    itineraries, answers = {}, {}
    async with connect_mcp():
        with patch("app.agents.itinerary_graph.load_trip", _load_golden_trip):
            for case in DATASET["itineraries"]:
                itineraries[case["name"]] = await generate_itineraries(
                    UUID(case["trip"]["trip_id"]), case["user_request"], save=False
                )
        for case in DATASET["adversarial"]:
            answers[case["name"]] = (await agent_services.chat(case["input"]))["answer"]
    return itineraries, answers


@pytest.fixture(scope="session")
def live_results() -> tuple[dict, dict]:
    return asyncio.run(_run_workflows())
