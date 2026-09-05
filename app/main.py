"""
Athenaeum — RAG Library Assistant API & Static Web Server
Built with FastAPI and Uvicorn.
"""

import os
import logging
from typing import List
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import STATIC_DIR
from app.rag.retriever import retrieve, load_index_and_metadata
from app.rag.generator import generate_answer
from app.rag.ingest import build_index

# Setup Server-side Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("athenaeum.api")

app = FastAPI(
    title="Athenaeum — RAG Library Assistant",
    description="FastAPI backend serving the RAG retrieval pipeline and static library interface."
)

# CORS Configuration
# Note: Allow all origins for development and local testing. Restrict to specific domains in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Request / Response Models
class ChatRequest(BaseModel):
    query: str = Field(..., description="Patron's query regarding public library policies or services.")

class SourceCitation(BaseModel):
    doc: str = Field(..., description="Document source name and section.")
    snippet: str = Field(..., description="Short extract from the grounded documentation.")
    score: float = Field(..., description="Cosine similarity score.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded explanation for the patron.")
    sources: List[SourceCitation] = Field(default_factory=list, description="Referenced documentation citations.")

class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int

# Mount Static Files
static_path = Path(STATIC_DIR)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    logger.warning("Static directory not found at: %s", static_path)

@app.get("/", include_in_schema=False)
async def serve_root():
    """Serve the single-page Athenaeum frontend."""
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Index UI file not found in static folder.")

@app.get("/health")
def health_check():
    """Health check endpoint to report operational status to frontend nav bar."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat endpoint:
    1. Validates query
    2. Retrieves top-k matching policy documentation chunks
    3. Synthesizes grounded answer using Gemini (or canned response if no context matches)
    4. Returns formatted answer and source citations
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty or solely whitespace."
        )

    try:
        # Retrieve relevant documentation chunks
        retrieved_chunks = retrieve(query)

        # Generate grounded response
        answer = generate_answer(query, retrieved_chunks)

        # Format sources with truncated snippets (~150 chars) and clean doc names
        sources: List[SourceCitation] = []
        for chunk in retrieved_chunks:
            source_file = chunk.get("source_file", "library-docs")
            section = chunk.get("section")
            doc_label = f"{source_file} — {section}" if section else source_file

            raw_text = chunk.get("text", "").strip()
            snippet = raw_text[:150] + "…" if len(raw_text) > 150 else raw_text
            score = float(chunk.get("score", 0.0))

            sources.append(SourceCitation(
                doc=doc_label,
                snippet=snippet,
                score=score
            ))

        return ChatResponse(answer=answer, sources=sources)

    except Exception as exc:
        # Log complete stack trace server-side only; never leak internal keys or trace to user
        logger.error("Internal error processing /chat query '%s': %s", query, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong processing your question."
        )

@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint():
    """
    Ingest endpoint to trigger FAISS index re-creation.
    NOTE: In production, this endpoint MUST be protected with admin authorization.
    """
    try:
        summary = build_index()
        # Force reload in-memory retriever cache
        load_index_and_metadata(force_reload=True)
        return IngestResponse(
            status="ok",
            chunks_indexed=summary.get("chunks_indexed", 0)
        )
    except Exception as exc:
        logger.error("Error during index ingestion: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(exc)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
