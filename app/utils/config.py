import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Content locations ---
PDF_DIR = Path(os.getenv("PDF_DIR", BASE_DIR / "data" / "pdfs"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma_db"))

# --- Chroma ---
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "travel_knowledge_base")

# --- Embeddings ---
# Sentence-transformer model used to embed both chunks and queries.
# Downloads once on first run (needs internet access), then caches locally.
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
)

# --- Chunking ---
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))   # ~250-350 tokens
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))
# The Chroma collection uses cosine distance (0 = identical, 2 = opposite).
# Chunks with a distance above this are treated as "not relevant enough".
# Sentence-transformer embeddings tend to cluster tighter than TF-IDF ones,
# so re-check this threshold against real query/answer pairs once you have
# a live collection - it may need to come down from this starting value.
MAX_RELEVANT_DISTANCE = float(os.getenv("MAX_RELEVANT_DISTANCE", "1.0"))

# --- Claude ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
