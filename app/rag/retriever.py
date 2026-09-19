"""
Vector similarity retriever module for Athenaeum.
Uses fastembed ONNX runtime, FAISS index, and lru_cache for query embeddings.
"""

import os
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
    CHUNKS_JSON_PATH
)

logger = logging.getLogger("athenaeum.retriever")

def get_rss_mb() -> float:
    """Return process resident memory in megabytes."""
    return psutil.Process().memory_info().rss / (1024 * 1024)

def log_rss(stage: str):
    """Log current RSS memory usage."""
    logger.info("[Memory] %s: RSS = %.2f MB", stage, get_rss_mb())

# Log memory after imports
log_rss("After retriever imports")

# Module-level singletons
_embedding_model: Optional[TextEmbedding] = None
_cached_index: Optional[faiss.Index] = None
_cached_chunks: Optional[List[Dict[str, Any]]] = None
_first_query_logged: bool = False

def get_embedding_model() -> TextEmbedding:
    """Load and return module-level singleton TextEmbedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Initializing fastembed model: %s (cache_dir=%s)", EMBEDDING_MODEL, MODEL_CACHE_DIR)
        _embedding_model = TextEmbedding(
            model_name=EMBEDDING_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            threads=1
        )
        log_rss("After embedding model load")
    return _embedding_model

def load_index_and_metadata():
    """
    Load pre-built FAISS index and chunk metadata from disk.
    Fails fast if index files are missing (no build-on-boot).
    """
    global _cached_index, _cached_chunks
    if _cached_index is not None and _cached_chunks is not None:
        return _cached_index, _cached_chunks

    faiss_file = Path(FAISS_INDEX_PATH)
    chunks_file = Path(CHUNKS_JSON_PATH)

    if not faiss_file.exists() or not chunks_file.exists():
        raise FileNotFoundError(
            f"Pre-built index files missing.\n"
            f"Expected:\n"
            f"  - {faiss_file}\n"
            f"  - {chunks_file}\n"
            "Build-on-boot is disabled to protect Render free-tier RAM.\n"
            "Please run 'python scripts/build_index.py' to generate and commit the index files."
        )

    try:
        _cached_index = faiss.read_index(str(faiss_file))
        with open(chunks_file, "r", encoding="utf-8") as f:
            _cached_chunks = json.load(f)

        log_rss("After FAISS index & metadata load")
        return _cached_index, _cached_chunks
    except Exception as e:
        raise RuntimeError(f"Error loading index or chunks: {e}")

@lru_cache(maxsize=256)
def _embed_query_cached(query_text: str) -> tuple:
    """Embed query with fastembed and cache representation as a tuple."""
    model = get_embedding_model()
    # Fastembed embed returns a generator
    raw_emb = next(model.embed([query_text])).astype(np.float32)
    return tuple(raw_emb.tolist())

def get_query_embedding(query: str) -> np.ndarray:
    """Get query embedding, L2 normalize, and return as (1, dim) float32 numpy array."""
    emb_tuple = _embed_query_cached(query)
    q_emb = np.array([emb_tuple], dtype=np.float32)
    faiss.normalize_L2(q_emb)
    return q_emb

def retrieve(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Retrieve top-k matching document chunks for the query using FAISS cosine similarity.
    """
    global _first_query_logged
    if not query or not query.strip():
        return []

    index, chunks = load_index_and_metadata()
    q_emb = get_query_embedding(query.strip())

    actual_k = min(top_k, index.ntotal)
    if actual_k <= 0:
        return []

    scores, indices = index.search(q_emb, actual_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        sim_score = float(score)
        if sim_score >= MIN_SIMILARITY:
            if idx < len(chunks):
                chunk_data = dict(chunks[idx])
                chunk_data["score"] = round(sim_score, 4)
                results.append(chunk_data)

    results.sort(key=lambda x: x["score"], reverse=True)

    if not _first_query_logged:
        _first_query_logged = True
        log_rss("After first query execution")

    return results
