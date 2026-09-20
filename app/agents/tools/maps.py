"""Maps tools — place lookup and point-to-point distance via OpenStreetMap.

Nominatim is keyless but rate limited to roughly one request per second and
requires an identifying User-Agent, both of which are handled here.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.tools.geocoding import geocode
from app.agents.tools.http import ToolHTTPError, get_json
from app.core.config import settings

EARTH_RADIUS_KM = 6371.0
# Rough door-to-door speeds used to turn a straight-line distance into a
# planning-grade duration. Deliberately conservative.
WALK_KMH = 4.5
CITY_DRIVE_KMH = 25.0
INTERCITY_DRIVE_KMH = 55.0


class FindPlacesInput(BaseModel):
    query: str = Field(
        description="What to look for, e.g. 'art museums', 'coffee', 'Kigali Genocide Memorial'."
    )
    destination: str = Field(
        description="City or area to search within, e.g. 'Kigali'."
    )
    limit: int = Field(
        default=6, ge=1, le=10, description="How many places to return."
    )


class DistanceInput(BaseModel):
    origin: str = Field(description="Starting place name or address.")
    destination: str = Field(description="Destination place name or address.")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


@tool("find_places", args_schema=FindPlacesInput)
async def find_places(query: str, destination: str, limit: int = 6) -> dict:
    """Find real, existing places (attractions, museums, restaurants, parks) in a destination.

    Use this to ground an itinerary in places that actually exist rather than
    relying on memory, and to get each place's address, coordinates and category.

    Results come from OpenStreetMap, so coverage is best for well-known and
    mapped locations. An empty `places` list means OpenStreetMap has no match —
    it does not prove the place does not exist, so say so rather than asserting
    a place is closed or fictional.
    """
    try:
        payload = await get_json(
            settings.NOMINATIM_URL,
            {
                "q": f"{query}, {destination}",
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
            },
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
        )
    except ToolHTTPError as exc:
        return {"error": str(exc), "query": query, "destination": destination}

    places = [
        {
            "name": hit.get("name") or hit.get("display_name", "").split(",")[0],
            "address": hit.get("display_name"),
            "category": hit.get("category"),
            "type": hit.get("type"),
            "latitude": float(hit["lat"]),
            "longitude": float(hit["lon"]),
        }
        for hit in payload
        if hit.get("lat") and hit.get("lon")
    ]

    return {
        "query": query,
        "destination": destination,
        "count": len(places),
        "places": places,
        "note": (
            "No OpenStreetMap match. Do not claim these places do not exist — "
            "just note they could not be verified."
            if not places
            else "Addresses and coordinates are from OpenStreetMap."
        ),
    }


@tool("get_distance_between", args_schema=DistanceInput)
async def get_distance_between(origin: str, destination: str) -> dict:
    """Estimate the distance and travel time between two places.

    Use this to check that activities scheduled on the same day are actually
    close enough to combine, and to warn the user when a day requires a long
    transfer.

    Distances are straight-line ("as the crow flies"); real road distance is
    typically 20-40% longer, which the returned durations already allow for.
    """
    try:
        start, end = await geocode(origin), await geocode(destination)
    except ToolHTTPError as exc:
        return {"error": str(exc), "origin": origin, "destination": destination}

    straight_km = _haversine_km(
        start.latitude, start.longitude, end.latitude, end.longitude
    )
    # Road-factor the straight line before converting to a duration.
    road_km = straight_km * 1.3
    drive_kmh = CITY_DRIVE_KMH if road_km <= 20 else INTERCITY_DRIVE_KMH

    return {
        "origin": f"{start.name}, {start.country}" if start.country else start.name,
        "destination": f"{end.name}, {end.country}" if end.country else end.name,
        "straight_line_km": round(straight_km, 1),
        "estimated_road_km": round(road_km, 1),
        "estimated_drive_minutes": round(road_km / drive_kmh * 60),
        "estimated_walk_minutes": (
            round(road_km / WALK_KMH * 60) if road_km <= 5 else None
        ),
        "same_day_friendly": road_km <= 60,
        "note": "Straight-line distance with a 1.3x road factor — not a routed itinerary.",
    }
