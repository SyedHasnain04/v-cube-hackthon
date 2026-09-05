"""
Configuration settings for Athenaeum RAG Assistant.
Loads environment variables and sets RAG pipeline constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

# Load .env file from project root
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Retrieve Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_api_key() -> str:
    """
    Validate and return GEMINI_API_KEY.
    Raises clear startup error if missing or set to placeholder.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key or key == "your_gemini_api_key_here":
        raise RuntimeError(
            "CRITICAL: GEMINI_API_KEY is not set or is using the default placeholder.\n"
            "Please create/update your .env file with a valid key:\n"
            "  GEMINI_API_KEY=your_actual_key"
        )
    return key

# Document & Ingestion Constants
CHUNK_SIZE: int = 400            # tokens/words
CHUNK_OVERLAP: int = 50          # overlapping words between chunks
TOP_K: int = 4                   # top k retrieved chunks
MIN_SIMILARITY: float = 0.35     # minimum cosine similarity threshold
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
GEMINI_MODEL: str = "gemini-2.5-flash"

# Directories
INDEX_DIR: str = str(APP_DIR / "data" / "index")
DOCS_DIR: str = str(APP_DIR / "data" / "docs")
STATIC_DIR: str = str(PROJECT_ROOT / "static")
