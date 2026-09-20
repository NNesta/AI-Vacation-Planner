"""Weather tool — Open-Meteo forecast, with a climate-normals fallback.

Open-Meteo only forecasts ~16 days ahead. Trips are usually planned further out
than that, so when the requested window is out of forecast range we fall back to
what the weather actually did on the same calendar dates in the three previous
years and label the answer ``historical_average``. The agent is told which kind
of data it got so it does not present a seasonal average as a forecast.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from statistics import mean

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.tools.geocoding import geocode
from app.agents.tools.http import ToolHTTPError, get_json
from app.core.config import settings

FORECAST_HORIZON_DAYS = 16
HISTORY_YEARS = 3
MAX_DAYS_RETURNED = 14

# WMO weather interpretation codes (https://open-meteo.com/en/docs).
WMO_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}

DAILY_FIELDS = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_sum,precipitation_probability_max"
)
ARCHIVE_FIELDS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"


class WeatherInput(BaseModel):
    destination: str = Field(
        description="City, park or region to check, e.g. 'Kigali' or 'Volcanoes National Park'."
    )
    start_date: str | None = Field(
        default=None,
        description="First day to report, as YYYY-MM-DD. Defaults to today.",
    )
    end_date: str | None = Field(
        default=None,
        description="Last day to report, as YYYY-MM-DD. Defaults to 6 days after start_date.",
    )


def _parse_date(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ToolHTTPError(f"{value!r} is not a valid YYYY-MM-DD date") from exc


def _describe(code: int | None) -> str:
    if code is None:
        return "unknown"
    return WMO_CODES.get(int(code), f"weather code {int(code)}")


def _rain_flag(precipitation_mm: float | None, probability: float | None) -> bool:
    """Whether the day should be treated as wet for activity planning."""
    if probability is not None and probability >= 50:
        return True
    return precipitation_mm is not None and precipitation_mm >= 2.0


async def _forecast(point, start: date, end: date) -> list[dict]:
    payload = await get_json(
        settings.OPEN_METEO_FORECAST_URL,
        {
            "latitude": point.latitude,
            "longitude": point.longitude,
            "daily": DAILY_FIELDS,
            "timezone": point.timezone or "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )
    daily = payload.get("daily") or {}
    days = []
    for i, day in enumerate(daily.get("time", [])):
        rain_mm = daily["precipitation_sum"][i]
        probability = daily["precipitation_probability_max"][i]
        days.append(
            {
                "date": day,
                "conditions": _describe(daily["weather_code"][i]),
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "precipitation_mm": rain_mm,
                "rain_probability_pct": probability,
                "likely_wet": _rain_flag(rain_mm, probability),
            }
        )
    return days


async def _archive_year(point, start: date, end: date, years_back: int) -> list[dict]:
    """Observed weather for the same calendar window ``years_back`` years ago."""
    try:
        shifted_start = start.replace(year=start.year - years_back)
        shifted_end = end.replace(year=end.year - years_back)
    except ValueError:  # 29 February in a non-leap year
        shifted_start = start.replace(year=start.year - years_back, day=28)
        shifted_end = end.replace(year=end.year - years_back, day=28)

    payload = await get_json(
        settings.OPEN_METEO_ARCHIVE_URL,
        {
            "latitude": point.latitude,
            "longitude": point.longitude,
            "daily": ARCHIVE_FIELDS,
            "timezone": point.timezone or "auto",
            "start_date": shifted_start.isoformat(),
            "end_date": shifted_end.isoformat(),
        },
    )
    daily = payload.get("daily") or {}
    return [
        {
            "offset": i,
            "weather_code": daily["weather_code"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
        }
        for i, _ in enumerate(daily.get("time", []))
    ]


def _average(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return round(mean(present), 1) if present else None


async def _climate_normals(point, start: date, end: date) -> list[dict]:
    """Average the same window across the last ``HISTORY_YEARS`` years."""
    per_year = await asyncio.gather(
        *(_archive_year(point, start, end, n) for n in range(1, HISTORY_YEARS + 1)),
        return_exceptions=True,
    )
    usable = [year for year in per_year if isinstance(year, list) and year]
    if not usable:
        raise ToolHTTPError("no historical weather available for this destination")

    span = (end - start).days + 1
    days = []
    for offset in range(span):
        samples = [
            day
            for year in usable
            for day in year
            if day["offset"] == offset
        ]
        if not samples:
            continue
        rain_mm = _average([s["precipitation_mm"] for s in samples])
        codes = [int(s["weather_code"]) for s in samples if s["weather_code"] is not None]
        days.append(
            {
                "date": (start + timedelta(days=offset)).isoformat(),
                "conditions": _describe(max(set(codes), key=codes.count) if codes else None),
                "temp_max_c": _average([s["temp_max_c"] for s in samples]),
                "temp_min_c": _average([s["temp_min_c"] for s in samples]),
                "precipitation_mm": rain_mm,
                "rain_probability_pct": None,
                "likely_wet": _rain_flag(rain_mm, None),
            }
        )
    return days


@tool("get_weather_forecast", args_schema=WeatherInput)
async def get_weather_forecast(
    destination: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Get day-by-day weather for a destination so activities can be matched to conditions.

    Use this whenever the user mentions weather, rain, the season, what to pack,
    or asks for "weather-friendly" plans, and before finalising any outdoor
    itinerary.

    Returns a `source` field that is either `forecast` (real forecast, within 16
    days) or `historical_average` (typical weather for those calendar dates,
    averaged over the last 3 years). Never describe a `historical_average`
    result as a forecast — call it typical or seasonal weather.

    Each day carries conditions, max/min temperature in Celsius, precipitation
    and a `likely_wet` flag you can use to pick indoor alternatives.
    """
    today = date.today()
    try:
        start = _parse_date(start_date, today)
        end = _parse_date(end_date, start + timedelta(days=6))
        if end < start:
            start, end = end, start
        end = min(end, start + timedelta(days=MAX_DAYS_RETURNED - 1))

        point = await geocode(destination)
        within_horizon = (start - today).days <= FORECAST_HORIZON_DAYS

        if within_horizon:
            days = await _forecast(point, max(start, today), end)
            source = "forecast"
        else:
            days = await _climate_normals(point, start, end)
            source = "historical_average"
    except ToolHTTPError as exc:
        return {"error": str(exc), "destination": destination}

    if not days:
        return {
            "error": "no weather data returned for this date range",
            "destination": destination,
        }

    wet_days = [d["date"] for d in days if d["likely_wet"]]
    return {
        "destination": f"{point.name}, {point.country}" if point.country else point.name,
        "source": source,
        "note": (
            "Real forecast."
            if source == "forecast"
            else f"Typical weather for these dates, averaged over the last {HISTORY_YEARS} years."
        ),
        "days": days,
        "wet_days": wet_days,
        "summary": (
            f"{len(wet_days)} of {len(days)} days look wet — plan indoor backups for those."
            if wet_days
            else "No notably wet days; outdoor activities should be fine throughout."
        ),
    }
