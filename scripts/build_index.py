"""
Offline FAISS index build script for Athenaeum.
Chunks library docs, embeds with fastembed (ONNX), and writes faiss.index and chunks.json.
These generated artifacts are committed to Git so runtime never embeds document chunks.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import faiss
from fastembed import TextEmbedding

from app.config import (
    DOCS_DIR,
    INDEX_DIR,
    FAISS_INDEX_PATH,
    CHUNKS_JSON_PATH,
    EMBEDDING_MODEL,
    MODEL_CACHE_DIR
)
from app.rag.ingest import load_documents, chunk_text

def build_offline_index():
    print("========================================")
    print(" Athenaeum Offline Index Builder")
    print("========================================")
    print(f"Reading documentation from : {DOCS_DIR}")
    docs = load_documents(DOCS_DIR)
    if not docs:
        raise RuntimeError(f"No documents found in {DOCS_DIR}!")

    all_chunks = []
    chunk_counter = 0
    for doc in docs:
        doc_chunks = chunk_text(doc["text"], doc["source_file"])
        for chunk in doc_chunks:
            chunk["id"] = chunk_counter
            all_chunks.append(chunk)
            chunk_counter += 1

    print(f"Total chunks created       : {len(all_chunks)}")

    print(f"Initializing fastembed model: {EMBEDDING_MODEL} (cache_dir={MODEL_CACHE_DIR})")
    model = TextEmbedding(
        model_name=EMBEDDING_MODEL,
        cache_dir=MODEL_CACHE_DIR,
        threads=1
    )

    chunk_texts = [c["text"] for c in all_chunks]
    print(f"Embedding {len(chunk_texts)} chunks...")
    embeddings = np.array(list(model.embed(chunk_texts)), dtype="float32")

    # L2 normalize embeddings so Inner Product = Cosine Similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Ensure target output directory exists
    os.makedirs(INDEX_DIR, exist_ok=True)

    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    index_size = os.path.getsize(FAISS_INDEX_PATH)
    chunks_size = os.path.getsize(CHUNKS_JSON_PATH)

    print("----------------------------------------")
    print(f"[OK] FAISS index written  : {FAISS_INDEX_PATH} ({index_size} bytes)")
    print(f"[OK] Chunks JSON written  : {CHUNKS_JSON_PATH} ({chunks_size} bytes)")
    print(f"[OK] Total vectors stored : {index.ntotal}")
    print(f"[OK] Vector dimensions    : {dimension}")
    print("Offline index build completed successfully.")
    print("========================================")

if __name__ == "__main__":
    build_offline_index()
