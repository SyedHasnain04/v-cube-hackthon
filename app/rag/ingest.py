"""
Document ingestion and FAISS vector index building module for Athenaeum.
Loads markdown/text policy documents, chunks them, computes embeddings, and builds FAISS index.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

from app.config import (
    DOCS_DIR,
    INDEX_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL
)

def load_documents(docs_dir: str = DOCS_DIR) -> List[Dict[str, str]]:
    """
    Read all .md and .txt files from the docs directory.
    Returns a list of dicts with 'source_file' and 'text'.
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        return []

    documents = []
    for file_path in sorted(docs_path.glob("*")):
        if file_path.suffix.lower() in [".md", ".txt"]:
            try:
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "source_file": file_path.name,
                    "text": content
                })
            except Exception as e:
                print(f"[Warning] Failed to read {file_path.name}: {e}")

    return documents

def chunk_text(text: str, source_file: str) -> List[Dict[str, Any]]:
    """
    Splits text on markdown headers (##, ###) into sections,
    then splits sections exceeding CHUNK_SIZE into overlapping word windows.
    Returns list of {text, source_file, section}.
    """
    chunks: List[Dict[str, Any]] = []
    # Split text into sections based on markdown ## and ### headers
    header_pattern = re.compile(r"^(#{2,3}\s+[^\n]+)", re.MULTILINE)
    parts = header_pattern.split(text)

    # If document has no ## or ### headers
    if len(parts) <= 1:
        sections = [("General", text.strip())]
    else:
        sections = []
        # Leading content before first header
        if parts[0].strip():
            sections.append(("Overview", parts[0].strip()))
        # Remaining paired elements (header, content)
        for i in range(1, len(parts), 2):
            raw_header = parts[i].strip()
            header_clean = re.sub(r"^#{2,3}\s*", "", raw_header).strip()
            section_content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections.append((header_clean, section_content))

    for section_title, content in sections:
        if not content:
            continue
        words = content.split()
        if len(words) <= CHUNK_SIZE:
            chunks.append({
                "text": content,
                "source_file": source_file,
                "section": section_title
            })
        else:
            # Overlapping window chunking
            start = 0
            step = CHUNK_SIZE - CHUNK_OVERLAP
            if step <= 0:
                step = CHUNK_SIZE
            while start < len(words):
                end = min(start + CHUNK_SIZE, len(words))
                chunk_words = words[start:end]
                chunks.append({
                    "text": " ".join(chunk_words),
                    "source_file": source_file,
                    "section": section_title
                })
                if end >= len(words):
                    break
                start += step

    return chunks

def build_index() -> Dict[str, Any]:
    """
    Builds and persists FAISS index and metadata chunks.json.
    Can be run via CLI or invoked from /ingest API route.
    """
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    print(f"Loading documents from: {DOCS_DIR}")
    docs = load_documents(DOCS_DIR)
    if not docs:
        raise RuntimeError(f"No documents found in {DOCS_DIR}. Please add .md or .txt files.")

    all_chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for doc in docs:
        doc_chunks = chunk_text(doc["text"], doc["source_file"])
        for chunk in doc_chunks:
            chunk["id"] = chunk_counter
            all_chunks.append(chunk)
            chunk_counter += 1

    if not all_chunks:
        raise RuntimeError("No chunks created from loaded documents.")

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    chunk_texts = [c["text"] for c in all_chunks]
    print(f"Embedding {len(chunk_texts)} chunks...")
    embeddings = model.encode(chunk_texts, show_progress_bar=False, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)

    # L2-normalize vectors so Inner Product = Cosine Similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Ensure index directory exists
    index_path = Path(INDEX_DIR)
    index_path.mkdir(parents=True, exist_ok=True)

    faiss_file = str(index_path / "faiss.index")
    chunks_file = str(index_path / "chunks.json")

    faiss.write_index(index, faiss_file)
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    index_size_bytes = os.path.getsize(faiss_file)

    summary = {
        "status": "ok",
        "docs_loaded": len(docs),
        "chunks_indexed": len(all_chunks),
        "index_dimension": dimension,
        "index_size_bytes": index_size_bytes,
        "index_path": faiss_file,
        "metadata_path": chunks_file
    }

    print("========================================")
    print(" Athenaeum Ingestion Complete")
    print(f" Documents Loaded : {summary['docs_loaded']}")
    print(f" Chunks Indexed   : {summary['chunks_indexed']}")
    print(f" Embedding Dim    : {summary['index_dimension']}")
    print(f" FAISS Index Size : {summary['index_size_bytes']} bytes")
    print(f" Index File       : {faiss_file}")
    print(f" Chunks File      : {chunks_file}")
    print("========================================")

    return summary

if __name__ == "__main__":
    build_index()
