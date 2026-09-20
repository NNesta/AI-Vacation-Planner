"""The itinerary workflow.

Phase 4 ran a fixed chain: trip details -> retrieve knowledge -> LLM response.
This replaces it with a graph in which an agent chooses the tools:

    START -> load_trip -> research -> draft -> review -+-> persist -> END
                            ^                          |
                            |     (agent <-> tools)    |
                            +------- redraft ----------+

``research`` is a full ReAct sub-agent: it decides which of the travel tools to
call and returns a brief. ``draft`` turns that brief into a schema-validated
itinerary via structured output. ``review`` applies business rules the schema
cannot express (right number of days, correct dates, budget respected) and loops
back with the specific complaints, up to ``ITINERARY_MAX_REVISIONS`` times.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.llm import get_chat_model
from app.agents.prompts import (
    DRAFT_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    REVISION_PROMPT,
    today_str,
)
from app.agents.state import AgentState, ItineraryState
from app.agents.tools import RESEARCH_TOOLS, load_trip
from app.core.config import settings
from app.schemas.itinerary.itinerary_request import LLMItineraryResponse

MAX_ACTIVITIES_PER_DAY = 6


def _build_research_agent() -> CompiledStateGraph:
    """A ReAct sub-graph limited to the fact-gathering tools."""
    model = get_chat_model().bind_tools(RESEARCH_TOOLS)

    async def agent(state: AgentState) -> dict:
        return {"messages": [await model.ainvoke(state["messages"])]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(RESEARCH_TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile()


def _research_brief(trip: dict, user_request: str | None) -> str:
    lines = [
        "Research this trip so an itinerary can be written for it.",
        "",
        f"Destination: {trip['destination']}",
        f"Dates: {trip['start_date']} to {trip['end_date']} ({trip['days']} days)",
        f"Travel style: {trip['trip_style']}",
        f"Budget: {trip['budget']} (total, USD)" if trip.get("budget") else "Budget: not set",
        f"Trip title: {trip['title']}",
    ]
    if trip.get("description"):
        lines.append(f"Traveller's notes: {trip['description']}")
    if user_request:
        lines += ["", f"The traveller specifically asked: {user_request}"]
    return "\n".join(lines)


def _review(trip: dict, days: list[dict]) -> list[str]:
    """Business rules the Pydantic schema cannot check. Returns complaints."""
    issues: list[str] = []
    expected = trip["days"]

    if not days:
        return ["The itinerary was empty. Produce a full day-by-day plan."]

    if len(days) != expected:
        issues.append(
            f"The trip is {expected} day(s) long but the draft has {len(days)}. "
            f"Produce exactly {expected}."
        )

    numbers = [d.get("day") for d in days]
    if numbers != list(range(1, len(days) + 1)):
        issues.append(
            f"Day numbers must run 1..{len(days)} in order, but got {numbers}."
        )

    start = date.fromisoformat(trip["start_date"])
    for index, day in enumerate(days):
        expected_date = (start + timedelta(days=index)).isoformat()
        if day.get("date") and day["date"] != expected_date:
            issues.append(
                f"Day {day.get('day', index + 1)} is dated {day['date']} but should be {expected_date}."
            )

        activities = day.get("activities") or []
        if not activities:
            issues.append(f"Day {day.get('day', index + 1)} has no activities.")
        elif len(activities) > MAX_ACTIVITIES_PER_DAY:
            issues.append(
                f"Day {day.get('day', index + 1)} has {len(activities)} activities; "
                f"keep it to at most {MAX_ACTIVITIES_PER_DAY}."
            )

        for activity in activities:
            if activity.get("start_time") and activity.get("end_time"):
                if activity["end_time"] <= activity["start_time"]:
                    issues.append(
                        f"On day {day.get('day', index + 1)}, "
                        f"{activity.get('title', 'an activity')} ends at or before it starts."
                    )

    return issues


def build_itinerary_graph() -> CompiledStateGraph:
    """Compile the itinerary workflow."""
    research_agent = _build_research_agent()
    drafter = get_chat_model().with_structured_output(LLMItineraryResponse)

    async def load(state: ItineraryState) -> dict:
        try:
            trip = await load_trip(UUID(state["trip_id"]))
        except ValueError:
            return {"error": f"{state['trip_id']!r} is not a valid trip id"}
        if trip is None:
            return {"error": f"no trip found with id {state['trip_id']}"}
        return {"trip": trip, "attempts": 0, "issues": []}

    async def research(state: ItineraryState) -> dict:
        trip = state["trip"]
        result = await research_agent.ainvoke(
            {
                "messages": [
                    SystemMessage(
                        content=RESEARCH_SYSTEM_PROMPT.format(today=today_str())
                    ),
                    HumanMessage(
                        content=_research_brief(trip, state.get("user_request"))
                    ),
                ]
            },
            {"recursion_limit": settings.AGENT_RECURSION_LIMIT},
        )
        # Imported here to keep graph.py's helpers in one place.
        from app.agents.graph import collect_tool_calls, final_text

        return {
            "research": final_text(result["messages"]),
            "tools_used": collect_tool_calls(result["messages"]),
        }

    async def draft(state: ItineraryState) -> dict:
        trip = state["trip"]
        system = SystemMessage(
            content=DRAFT_SYSTEM_PROMPT.format(
                today=today_str(),
                days=trip["days"],
                start_date=trip["start_date"],
            )
        )
        prompt = [
            f"Trip: {trip['title']} — {trip['destination']}",
            f"Dates: {trip['start_date']} to {trip['end_date']} ({trip['days']} days)",
            f"Style: {trip['trip_style']}   Budget: {trip.get('budget') or 'not set'} USD",
            "",
            "RESEARCH BRIEF",
            state.get("research") or "(research produced nothing usable)",
        ]
        if state.get("user_request"):
            prompt += ["", f"Traveller's request: {state['user_request']}"]
        if state.get("issues"):
            prompt += [
                "",
                REVISION_PROMPT.format(
                    issues="\n".join(f"- {i}" for i in state["issues"])
                ),
            ]

        try:
            result = await drafter.ainvoke([system, HumanMessage(content="\n".join(prompt))])
        except Exception as exc:
            return {
                "error": f"the model did not return a usable itinerary: {exc}",
                "attempts": state.get("attempts", 0) + 1,
            }

        return {
            "itinerary": [day.model_dump(mode="json") for day in result.itineraries],
            "attempts": state.get("attempts", 0) + 1,
        }

    async def review(state: ItineraryState) -> dict:
        if state.get("error"):
            return {}
        return {"issues": _review(state["trip"], state.get("itinerary") or [])}

    def after_load(state: ItineraryState) -> str:
        return END if state.get("error") else "research"

    def after_review(state: ItineraryState) -> str:
        if state.get("error"):
            return END
        if not state.get("issues"):
            return "persist" if state.get("save") else END
        if state.get("attempts", 0) > settings.ITINERARY_MAX_REVISIONS:
            # Out of revisions: keep the best draft and report what is wrong
            # rather than failing the request outright.
            return "persist" if state.get("save") else END
        return "draft"

    async def persist(state: ItineraryState) -> dict:
        from app.services.itinerary import replace_trip_itineraries

        try:
            await replace_trip_itineraries(
                UUID(state["trip_id"]), state.get("itinerary") or []
            )
        except Exception as exc:
            return {"saved": False, "error": f"could not save the itinerary: {exc}"}
        return {"saved": True}

    builder = StateGraph(ItineraryState)
    builder.add_node("load_trip", load)
    builder.add_node("research", research)
    builder.add_node("draft", draft)
    builder.add_node("review", review)
    builder.add_node("persist", persist)

    builder.add_edge(START, "load_trip")
    builder.add_conditional_edges("load_trip", after_load, {"research": "research", END: END})
    builder.add_edge("research", "draft")
    builder.add_edge("draft", "review")
    builder.add_conditional_edges(
        "review", after_review, {"draft": "draft", "persist": "persist", END: END}
    )
    builder.add_edge("persist", END)

    return builder.compile()


@lru_cache(maxsize=1)
def get_itinerary_graph() -> CompiledStateGraph:
    return build_itinerary_graph()
