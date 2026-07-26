from collections.abc import Iterable

from anthropic import Omit
from anthropic.types import MessageParam, TextBlockParam

from app.ai.providers.anthropic import client
from app.core.config import settings


def call_llm(
    max_tokens: int,
    messages: Iterable[MessageParam],
    system: str | Iterable[TextBlockParam] | Omit = None,
    temperature: float | Omit = 1.0,
    stop_sequences: str | Omit = None,
) -> str:
    params = {
        "model": settings.LLM_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if system:
        params["system"] = system
    response = client.messages.create(**params)
    return response.content[0].text
