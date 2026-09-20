"""Single place where the chat model is configured.

Everything in ``app/agents`` goes through here so the model id, temperature and
token budget are changed in one spot (``app/core/config.py``).
"""

from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from app.core.config import settings


@lru_cache(maxsize=4)
def get_chat_model(
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatAnthropic:
    """Return a cached ``ChatAnthropic`` client.

    The client is stateless and thread safe, so caching it avoids rebuilding an
    HTTP client on every request.
    """
    return ChatAnthropic(
        model=settings.LLM_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        max_tokens=settings.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
        timeout=None,
        stop=None,
    )
