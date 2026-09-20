import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


PDF_DIR = Path(os.getenv("PDF_DIR", BASE_DIR / "data" / "pdfs"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma_db"))

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "travel_knowledge_base")

SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
)

CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))   # ~250-350 tokens
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))

TOP_K = int(os.getenv("TOP_K", "4"))

MAX_RELEVANT_DISTANCE = float(os.getenv("MAX_RELEVANT_DISTANCE", "1.0"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
