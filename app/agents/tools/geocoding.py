"""Place-name -> coordinates, shared by the weather and maps tools."""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.tools.http import ToolHTTPError, get_json
from app.core.config import settings


@dataclass(frozen=True)
class GeoPoint:
    name: str
    country: str | None
    latitude: float
    longitude: float
    timezone: str | None = None


async def geocode(place: str) -> GeoPoint:
    """Resolve a free-text place name to coordinates via Open-Meteo geocoding."""
    payload = await get_json(
        settings.OPEN_METEO_GEOCODING_URL,
        {"name": place, "count": 1, "language": "en", "format": "json"},
    )
    results = payload.get("results") or []
    if not results:
        raise ToolHTTPError(f"no place named {place!r} could be found")

    hit = results[0]
    return GeoPoint(
        name=hit.get("name", place),
        country=hit.get("country"),
        latitude=float(hit["latitude"]),
        longitude=float(hit["longitude"]),
        timezone=hit.get("timezone"),
    )
