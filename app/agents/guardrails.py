"""Deterministic safety checks around the model.

Regexes stop the obvious attacks before any tokens are spent. Whatever gets past
them is handled by ``SECURITY_RULES`` in the system prompts.
"""

from __future__ import annotations

import re
import unicodedata

from fastapi import HTTPException, status

from app.agents.prompts import (
    AGENT_SYSTEM_PROMPT,
    DRAFT_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    SECURITY_RULES,
)
from app.core.observability import logger

BLOCKED_TEXT = "[removed by safety filter]"
SAFE_ANSWER = "Sorry, I can't share that. I'm happy to help you plan a trip instead."

GUARDRAIL_RESPONSES = {
    400: {"description": "Blocked by a guardrail: prompt injection or an unsupported action."}
}

ZERO_WIDTH_CHARS = dict.fromkeys(map(ord, "​‌‍⁠﻿"))


def _compile(*patterns: str) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(p, re.DOTALL | re.MULTILINE) for p in patterns)


INJECTION_PATTERNS = _compile(
    r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,30}"
    r"\b(?:previous|prior|above|earlier|all|your|system|safety|any)\b.{0,20}"
    r"\b(?:instructions?|prompts?|rules|guidelines|guardrails|restrictions)\b",
    r"\b(?:reveal|show|print|repeat|output|display|tell me|what.s|what is|what are)\b.{0,40}"
    r"\b(?:system|initial|hidden|developer|original)\s+(?:prompt|instructions?|message|rules)\b",
    r"\byou are now\b",
    r"\bnew instructions\b",
    r"\b(?:jailbreak|jailbroken|developer mode|dan mode|do anything now)\b",
    r"\b(?:pretend|act as if|imagine)\b.{0,30}\b(?:no|without)\b.{0,20}"
    r"\b(?:rules|restrictions|filters|limits)\b",
    r"^\s*(?:system|assistant)\s*:",
    r"<\s*/?\s*(?:system|assistant|instructions?)\s*>",
    r"\[/?(?:system|inst)\]",
)

UNSUPPORTED_ACTION_PATTERNS = _compile(
    r"\b(?:drop|truncate|wipe|delete|erase)\b.{0,30}"
    r"\b(?:database|tables?|all (?:the )?(?:users?|trips?|records?))\b",
    r"\b(?:run|execute)\b.{0,30}\b(?:sql|shell|bash|commands?|scripts?|code)\b",
    r"\b(?:book|reserve|purchase|buy|pay for)\b.{0,50}\b(?:for me|on my behalf)\b",
    r"\b(?:charge|bill)\b.{0,30}\b(?:card|account)\b",
    r"\b(?:show|give|reveal|tell|share|print|list|send)\b.{0,40}"
    r"\b(?:api[ _-]?keys?|secret[ _-]?keys?|credentials|passwords?|access tokens?"
    r"|env(?:ironment)? variables?)\b",
)

SECRET_PATTERN = re.compile(r"sk-ant-[\w-]{8,}")

LEAK_MARKERS = tuple(
    prompt.strip().splitlines()[0].lower()
    for prompt in (
        AGENT_SYSTEM_PROMPT,
        RESEARCH_SYSTEM_PROMPT,
        DRAFT_SYSTEM_PROMPT,
        SECURITY_RULES,
    )
)


class GuardrailViolation(HTTPException):
    def __init__(self, code: str, message: str) -> None:
        logger.warning("guardrail_blocked code=%s", code)
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": code, "message": message},
        )


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(ZERO_WIDTH_CHARS).lower()


def _matches(patterns: tuple[re.Pattern, ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def check_input(text: str | None) -> None:
    """Reject user text that attacks the prompt or asks for something unsupported."""
    if not text:
        return
    normalized = _normalize(text)
    if _matches(INJECTION_PATTERNS, normalized):
        raise GuardrailViolation(
            "prompt_injection",
            "This request was blocked because it tries to change the assistant's instructions.",
        )
    if _matches(UNSUPPORTED_ACTION_PATTERNS, normalized):
        raise GuardrailViolation(
            "unsupported_action",
            "I can research and plan trips, but I can't make bookings, take payments "
            "or touch system data.",
        )


def sanitize_untrusted(text: str | None) -> str | None:
    """Neutralise stored text that is about to be placed in front of the model."""
    if text and _matches(INJECTION_PATTERNS, _normalize(text)):
        logger.warning("guardrail_blocked code=indirect_injection")
        return BLOCKED_TEXT
    return text


def check_output(answer: str) -> str:
    """Replace an answer that leaks the system prompt or a credential."""
    normalized = _normalize(answer)
    if SECRET_PATTERN.search(answer) or any(m in normalized for m in LEAK_MARKERS):
        logger.warning("guardrail_blocked code=output_leak")
        return SAFE_ANSWER
    return answer
