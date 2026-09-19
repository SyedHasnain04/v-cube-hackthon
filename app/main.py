"""
Athenaeum — RAG Library Assistant API & Static Web Server
Built with FastAPI and Uvicorn.
"""

import logging
from typing import List
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Configure logging FIRST — retriever.py fires log_rss("after-imports") at
# module import time; we want that captured by basicConfig, not dropped.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("athenaeum.api")

# Import retriever AFTER basicConfig so its module-level log_rss is captured.
from app.config import STATIC_DIR
from app.rag import retriever as _retriever
from app.rag.generator import generate_answer

app = FastAPI(
    title="Athenaeum — RAG Library Assistant",
    description="FastAPI backend serving the RAG retrieval pipeline and static library interface.",
)

# CORS — allow all origins (restrict to specific domain in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(..., description="Patron's question about library policies or services.")

class SourceCitation(BaseModel):
    doc: str = Field(..., description="Document source name and section.")
    snippet: str = Field(..., description="Short extract from the grounded documentation.")
    score: float = Field(..., description="Cosine similarity score.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded explanation for the patron.")
    sources: List[SourceCitation] = Field(default_factory=list)

class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int

# ---------------------------------------------------------------------------
# Startup — blocks Uvicorn from accepting requests until both model & index
# are fully loaded.  Any OOM or missing-file error crashes here with a clear
# log rather than surfacing silently on the first user query.
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    logger.info("[Startup] Athenaeum backend initialising...")
    _retriever.initialise()   # loads model + index, logs RSS at each stage
    logger.info("[Startup] Ready — model and index loaded.")

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

static_path = Path(STATIC_DIR)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    logger.warning("[Startup] Static directory not found at: %s", static_path)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_root():
    """Serve the single-page Athenaeum frontend."""
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Frontend index.html not found.")


@app.get("/health")
def health_check():
    """
    Returns 200 only after the embedding model and FAISS index are fully loaded.
    Returns 503 while startup is still in progress or if initialisation failed.
    The frontend polls this to know when the backend is ready to answer queries.
    """
    if not _retriever.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend is still initialising — model or index not yet loaded.",
        )
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat:
    1. Retrieve top-k matching policy chunks via FAISS cosine search.
    2. Synthesise a grounded answer with Gemini.
    3. Return answer + cited source passages.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    try:
        retrieved_chunks = _retriever.retrieve(query)
        answer = generate_answer(query, retrieved_chunks)

        sources: List[SourceCitation] = []
        for chunk in retrieved_chunks:
            source_file = chunk.get("source_file", "library-docs")
            section = chunk.get("section")
            doc_label = f"{source_file} — {section}" if section else source_file
            raw_text = chunk.get("text", "").strip()
            snippet = raw_text[:150] + "\u2026" if len(raw_text) > 150 else raw_text
            sources.append(SourceCitation(
                doc=doc_label,
                snippet=snippet,
                score=float(chunk.get("score", 0.0)),
            ))

        return ChatResponse(answer=answer, sources=sources)

    except Exception as exc:
        logger.error("Error in /chat for query '%s': %s", query, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong processing your question.",
        )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint():
    """
    Rebuild FAISS index from docs directory and reload into memory.
    NOTE: protect this with admin auth before going to production.
    """
    try:
        from scripts.build_index import build_offline_index
        build_offline_index()
        # Reset singletons so the next retrieve() picks up fresh files
        _retriever._embedding_model = None
        _retriever._cached_index = None
        _retriever._cached_chunks = None
        _retriever._ready = False
        _retriever.initialise()
        chunks = _retriever._cached_chunks or []
        return IngestResponse(status="ok", chunks_indexed=len(chunks))
    except Exception as exc:
        logger.error("Ingest failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
