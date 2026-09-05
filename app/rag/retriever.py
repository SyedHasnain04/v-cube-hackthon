"""
Vector similarity retriever module for Athenaeum.
Loads FAISS index and chunk metadata, embeds incoming query, and returns top-k matching chunks.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import (
    INDEX_DIR,
    TOP_K,
    MIN_SIMILARITY,
    EMBEDDING_MODEL
)

_cached_index = None
_cached_chunks = None
_cached_model = None

def get_embedding_model():
    """Lazily load and cache the SentenceTransformer model."""
    global _cached_model
    if _cached_model is None:
        from sentence_transformers import SentenceTransformer
        _cached_model = SentenceTransformer(EMBEDDING_MODEL)
    return _cached_model

def load_index_and_metadata(force_reload: bool = False):
    """
    Load the FAISS index and chunk metadata from disk.
    Caches in memory for subsequent fast queries.
    Raises RuntimeError if index files are missing.
    """
    global _cached_index, _cached_chunks
    if not force_reload and _cached_index is not None and _cached_chunks is not None:
        return _cached_index, _cached_chunks

    import faiss

    index_dir_path = Path(INDEX_DIR)
    faiss_file = index_dir_path / "faiss.index"
    chunks_file = index_dir_path / "chunks.json"

    if not faiss_file.exists() or not chunks_file.exists():
        from app.rag.ingest import build_index
        print("[Athenaeum] Index files not found. Auto-building index from docs...")
        build_index()

    try:
        index = faiss.read_index(str(faiss_file))
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        _cached_index = index
        _cached_chunks = chunks
        return _cached_index, _cached_chunks
    except Exception as e:
        raise RuntimeError(f"Error loading index or chunks from {INDEX_DIR}: {e}")

def retrieve(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Embed query with SentenceTransformer, normalize L2, search FAISS index,
    and return filtered top-k results with cosine similarity score.
    """
    if not query or not query.strip():
        return []

    import numpy as np
    import faiss

    index, chunks = load_index_and_metadata()
    model = get_embedding_model()

    # Embed query
    q_emb = model.encode([query.strip()], show_progress_bar=False, convert_to_numpy=True)
    q_emb = q_emb.astype(np.float32)

    # Normalize vector for cosine similarity
    faiss.normalize_L2(q_emb)

    actual_k = min(top_k, index.ntotal)
    if actual_k <= 0:
        return []

    scores, indices = index.search(q_emb, actual_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        sim_score = float(score)
        # Filter by minimum similarity threshold
        if sim_score >= MIN_SIMILARITY:
            if idx < len(chunks):
                chunk_data = dict(chunks[idx])
                chunk_data["score"] = round(sim_score, 4)
                results.append(chunk_data)

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
