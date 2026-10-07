"""Tool registry.

``TRAVEL_TOOLS`` is what the agent is bound to; adding a tool here is all that
is needed for the model to start choosing it.
"""

from .knowledge import search_travel_knowledge
from .maps import find_places, get_distance_between
from .pricing import estimate_trip_cost
from .trips import get_saved_itinerary, get_trip_details, load_trip
from .weather import get_weather_forecast

TRAVEL_TOOLS = [
    get_trip_details,
    get_saved_itinerary,
    search_travel_knowledge,
]

# Subset used by the itinerary workflow's research step: reading a trip is done
# deterministically there, so those tools are left out.
RESEARCH_TOOLS = [
    search_travel_knowledge,
]

MCP_TOOLS = [
    get_weather_forecast,
    find_places,
    get_distance_between,
    estimate_trip_cost,
]

__all__ = [
    "TRAVEL_TOOLS",
    "RESEARCH_TOOLS",
    "MCP_TOOLS",
    "load_trip",
    "search_travel_knowledge",
    "get_weather_forecast",
    "find_places",
    "get_distance_between",
    "estimate_trip_cost",
    "get_trip_details",
    "get_saved_itinerary",
]
