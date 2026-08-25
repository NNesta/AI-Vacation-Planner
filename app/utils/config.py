import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Content locations ---
PDF_DIR = Path(os.getenv("PDF_DIR", BASE_DIR / "data" / "pdfs"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma_db"))
VECTORIZER_PATH = CHROMA_DIR / "tfidf_vectorizer.joblib"

# --- Chroma ---
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "travel_knowledge_base")

# --- Chunking ---
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))   # ~250-350 tokens
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))
# Chroma returns squared-L2 distance by default. Since our TF-IDF vectors are
# L2-normalized, this is monotonic with cosine distance. Chunks with a
# distance above this are treated as "not relevant enough".
MAX_RELEVANT_DISTANCE = float(os.getenv("MAX_RELEVANT_DISTANCE", "1.3"))

# --- Claude ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
