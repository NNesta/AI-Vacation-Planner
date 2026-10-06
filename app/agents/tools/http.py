"""Shared HTTP helper for the keyless external APIs the tools call."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class ToolHTTPError(RuntimeError):
    """Raised when an upstream tool API cannot be reached or returns an error."""


async def get_json(
    url: str, params: dict[str, Any], headers: dict[str, str] | None = None
) -> Any:
    """GET ``url`` and return parsed JSON, normalising failures to one exception."""
    try:
        async with httpx.AsyncClient(timeout=settings.TOOL_HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise ToolHTTPError(
            f"{exc.request.url.host} returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        # Some httpx errors stringify to "", which would leave the agent with a
        # blank reason; fall back to the exception class name.
        reason = str(exc) or type(exc).__name__
        raise ToolHTTPError(f"could not reach {url}: {reason}") from exc
    except ValueError as exc:  # malformed JSON
        raise ToolHTTPError(f"{url} returned a non-JSON response") from exc
