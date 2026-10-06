from __future__ import annotations

import subprocess
from functools import lru_cache
from tempfile import NamedTemporaryFile

import anyio
import edge_tts
import numpy as np
from aiohttp import ClientError
from edge_tts.exceptions import EdgeTTSException
from transformers import pipeline

from app.core.config import settings

SAMPLE_RATE = 16_000
SYNTHESIS_ERRORS = (EdgeTTSException, ClientError, TimeoutError)


@lru_cache(maxsize=1)
def _recognizer():
    return pipeline("automatic-speech-recognition", model=settings.STT_MODEL)


def _decode(audio: bytes) -> np.ndarray:
    with NamedTemporaryFile() as recording:
        recording.write(audio)
        recording.flush()
        decoded = subprocess.run(
            [
                "ffmpeg", "-i", recording.name,
                "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le",
                "-loglevel", "quiet", "pipe:1",
            ],
            capture_output=True,
        )
    samples = np.frombuffer(decoded.stdout, np.float32)
    if not samples.size:
        raise ValueError("unsupported or corrupted audio file")
    return samples


def _transcribe(audio: bytes) -> str:
    result = _recognizer()(
        {"raw": _decode(audio), "sampling_rate": SAMPLE_RATE},
        chunk_length_s=30,
        generate_kwargs={"task": "transcribe"},
    )
    return result["text"].strip()


async def transcribe(audio: bytes) -> str:
    return await anyio.to_thread.run_sync(_transcribe, audio)


async def synthesize(text: str) -> bytes:
    audio = bytearray()
    async for chunk in edge_tts.Communicate(text, settings.TTS_VOICE).stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)
