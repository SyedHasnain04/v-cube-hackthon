"""
Vector similarity retriever module for Athenaeum.
Uses fastembed ONNX runtime, FAISS index, and lru_cache for query embeddings.

RSS memory is logged at 4 points:
  1. After module-level imports resolve
  2. After the embedding model is loaded from disk
  3. After the FAISS index + chunks.json are read into RAM
  4. After the very first live query completes
"""

import json
import logging
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any, Optional

import numpy as np
import faiss
import psutil
from fastembed import TextEmbedding

from app.config import (
    TOP_K,
    MIN_SIMILARITY,
    EMBEDDING_MODEL,
    MODEL_CACHE_DIR,
    FAISS_INDEX_PATH,
    CHUNKS_JSON_PATH,
)

logger = logging.getLogger("athenaeum.retriever")

# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------

def get_rss_mb() -> float:
    """Return process resident set size in megabytes."""
    return psutil.Process().memory_info().rss / (1024 * 1024)


def log_rss(stage: str) -> None:
    """Emit a structured INFO log with current RSS."""
    logger.info("[Memory] %s | RSS = %.1f MB", stage, get_rss_mb())


# Log after imports — logger is configured by main.py before this module is
# imported, so basicConfig has already run by the time startup_event calls us.
log_rss("after-imports")

# ---------------------------------------------------------------------------
# Module-level singletons — set eagerly at startup, never lazily
# ---------------------------------------------------------------------------

_embedding_model: Optional[TextEmbedding] = None
_cached_index: Optional[faiss.Index] = None
_cached_chunks: Optional[List[Dict[str, Any]]] = None
_ready: bool = False          # set True only after both model AND index are loaded
_first_query_logged: bool = False


# ---------------------------------------------------------------------------
# Startup initialisation — called explicitly from main.startup_event()
# ---------------------------------------------------------------------------

def initialise() -> None:
    """
    Eagerly load the embedding model and FAISS index.
    Called once from the FastAPI startup hook so that any OOM or missing-file
    error crashes at boot (with a clear log) instead of on the first user query.
    Idempotent: safe to call more than once.
    """
    global _embedding_model, _cached_index, _cached_chunks, _ready

    if _ready:
        return

    # 1. Embedding model
    logger.info(
        "[Startup] Loading fastembed model: %s (cache_dir=%s, threads=1)",
        EMBEDDING_MODEL, MODEL_CACHE_DIR,
    )
    _embedding_model = TextEmbedding(
        model_name=EMBEDDING_MODEL,
        cache_dir=MODEL_CACHE_DIR,
        threads=1,
    )
    log_rss("after-model-load")

    # 2. FAISS index + chunk metadata
    faiss_file = Path(FAISS_INDEX_PATH)
    chunks_file = Path(CHUNKS_JSON_PATH)

    if not faiss_file.exists() or not chunks_file.exists():
        raise FileNotFoundError(
            "Pre-built index files missing.\n"
            f"  Expected: {faiss_file}\n"
            f"  Expected: {chunks_file}\n"
            "Build-on-boot is disabled to protect Render free-tier RAM.\n"
            "Run 'python scripts/build_index.py' locally, commit the outputs, and redeploy."
        )

    _cached_index = faiss.read_index(str(faiss_file))
    with open(chunks_file, "r", encoding="utf-8") as f:
        _cached_chunks = json.load(f)

    log_rss("after-index-load")
    logger.info(
        "[Startup] Index ready: %d vectors x %d dims | %d chunks loaded",
        _cached_index.ntotal, _cached_index.d, len(_cached_chunks),
    )

    _ready = True


def is_ready() -> bool:
    """Return True only when both model and index are loaded."""
    return _ready


# ---------------------------------------------------------------------------
# Query path — only reachable after initialise() has succeeded
# ---------------------------------------------------------------------------

@lru_cache(maxsize=256)
def _embed_query_cached(query_text: str) -> tuple:
    """
    Embed a single query string with fastembed.
    Result cached as a plain tuple so lru_cache can hash it.
    """
    raw_emb = next(_embedding_model.embed([query_text])).astype(np.float32)
    return tuple(raw_emb.tolist())


def _get_query_embedding(query: str) -> np.ndarray:
    """Return a (1, dim) float32 array, L2-normalised for IndexFlatIP cosine search."""
    emb_tuple = _embed_query_cached(query)
    q_emb = np.array([emb_tuple], dtype=np.float32)
    faiss.normalize_L2(q_emb)
    return q_emb


def retrieve(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Embed query, search FAISS index, filter by MIN_SIMILARITY, and return
    top-k results sorted by cosine score descending.
    """
    global _first_query_logged

    if not query or not query.strip():
        return []

    q_emb = _get_query_embedding(query.strip())
    actual_k = min(top_k, _cached_index.ntotal)
    if actual_k <= 0:
        return []

    scores, indices = _cached_index.search(q_emb, actual_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        sim_score = float(score)
        if sim_score >= MIN_SIMILARITY and idx < len(_cached_chunks):
            chunk_data = dict(_cached_chunks[idx])
            chunk_data["score"] = round(sim_score, 4)
            results.append(chunk_data)

    results.sort(key=lambda x: x["score"], reverse=True)

    if not _first_query_logged:
        _first_query_logged = True
        log_rss("after-first-query")

    return results
