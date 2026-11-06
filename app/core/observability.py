"""Logs latency, tokens, model and failures, and forwards traces to Datadog.

Logging always runs. Datadog LLM Observability starts only when ``DD_API_KEY`` is
set; it then auto-instruments the LangChain, LangGraph and MCP calls.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any
from uuid import UUID

from ddtrace import patch
from ddtrace.llmobs import LLMObs
from fastapi import Request, Response
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.core.config import settings

logger = logging.getLogger("vacation_planner")

AI_ROUTES = (
    "/api/v1/agent",
    "/api/v1/itineraries/generate",
    "/api/v1/itineraries/ask",
    "/api/v1/multimodal",
)


def setup_observability() -> None:
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    if settings.DD_API_KEY:
        # langchain-anthropic reads the raw HTTP response, which hides token usage
        # from ddtrace's anthropic integration, so LangChain reports the LLM spans.
        LLMObs.enable(
            ml_app=settings.DD_LLMOBS_ML_APP,
            service=settings.DD_LLMOBS_ML_APP,
            env=settings.DD_ENV,
            site=settings.DD_SITE,
            api_key=settings.DD_API_KEY.get_secret_value(),
            agentless_enabled=True,
            integrations_enabled=False,
        )
        patch(raise_errors=True, langchain=True, langgraph=True, mcp=True)


class LLMCallLogger(BaseCallbackHandler):
    run_inline = True

    def __init__(self) -> None:
        self._started: dict[UUID, float] = {}

    def _latency_ms(self, run_id: UUID) -> int:
        return round((perf_counter() - self._started.pop(run_id, perf_counter())) * 1000)

    def on_chat_model_start(
        self, serialized: dict, messages: list, *, run_id: UUID, **kwargs: Any
    ) -> None:
        self._started[run_id] = perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        message = response.generations[0][0].message
        usage = message.usage_metadata or {}
        logger.info(
            "llm_call model=%s latency_ms=%d input_tokens=%s output_tokens=%s",
            message.response_metadata.get("model", settings.LLM_MODEL),
            self._latency_ms(run_id),
            usage.get("input_tokens"),
            usage.get("output_tokens"),
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        logger.error(
            "llm_error model=%s latency_ms=%d error=%s",
            settings.LLM_MODEL,
            self._latency_ms(run_id),
            type(error).__name__,
        )


llm_call_logger = LLMCallLogger()


@contextmanager
def _ai_route_span(path: str) -> Iterator[Any]:
    route = next((r for r in AI_ROUTES if path.startswith(r)), None)
    if route is None or not LLMObs.enabled:
        yield None
        return
    with LLMObs.workflow(name=route) as span:
        yield span


async def observe_requests(request: Request, call_next) -> Response:
    path = request.url.path
    started = perf_counter()
    status_code = 500
    try:
        with _ai_route_span(path) as span:
            response = await call_next(request)
            status_code = response.status_code
            if span:
                LLMObs.annotate(span, tags={"http.status_code": status_code})
                span.error = int(status_code >= 500)
        return response
    finally:
        level = (
            logging.ERROR
            if status_code >= 500
            else logging.WARNING
            if status_code >= 400
            else logging.INFO
        )
        logger.log(
            level,
            "http_request method=%s path=%s status=%d latency_ms=%d",
            request.method,
            path,
            status_code,
            round((perf_counter() - started) * 1000),
        )
