"""
Athenaeum — RAG Library Assistant Backend
FastAPI server serving static assets and handling RAG chat queries.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Athenaeum Library Assistant API",
    description="RAG Library Assistant Backend delivering grounded answers from library documentation."
)

# Pydantic schemas according to backend contract
class ChatRequest(BaseModel):
    query: str

class SourceItem(BaseModel):
    doc: str
    snippet: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]

# In-memory library documentation for grounded RAG answers
LIBRARY_KNOWLEDGE_BASE = [
    {
        "doc": "Library Membership Guide (Section 1.2)",
        "content": (
            "Any resident with valid local photo ID and proof of address is eligible for a standard library card. "
            "Membership is free for residents, students, and educators. Non-residents may apply for an annual visitor card for $25. "
            "Members under 18 must have a parent or guardian co-sign their registration."
        ),
        "keywords": ["membership", "card", "join", "register", "eligibility", "sign up", "fee", "cost", "free"]
    },
    {
        "doc": "Circulation & Borrowing Policy (Section 2.1 - 2.4)",
        "content": (
            "Standard cardholders may borrow up to 10 physical books simultaneously, along with up to 3 audiovisual items (DVDs/audiobooks). "
            "The loan period is 21 days for general collection books and 7 days for high-demand new releases or multimedia items. "
            "Items with no waiting hold can be renewed up to two times online or in person."
        ),
        "keywords": ["borrow", "how many", "limit", "loan", "period", "renew", "renewal", "books", "at once", "days"]
    },
    {
        "doc": "Overdue & Lost Material Rules (Section 3.5)",
        "content": (
            "The library operates under a fine-free policy for most general circulating materials. Overdue reminders are issued at 7 and 14 days. "
            "If an item is overdue by more than 30 days, borrowing privileges are temporarily suspended and an automatic replacement fee is billed. "
            "Returning the overdue item in good condition immediately waives the replacement fee."
        ),
        "keywords": ["overdue", "fine", "late", "fee", "penalty", "lost", "suspended", "replacement", "damage"]
    },
    {
        "doc": "Digital Resources & E-Library Services (Section 4.1)",
        "content": (
            "Cardholders enjoy 24/7 access to digital resources including Libby/OverDrive for eBooks and audiobooks, Hoopla for streaming movies and music, "
            "and JSTOR and Gale academic databases for scholarly research. A active library card number and PIN are required to log in."
        ),
        "keywords": ["digital", "ebook", "audiobook", "libby", "overdrive", "online", "database", "hoopla", "jstor", "research", "remote"]
    },
    {
        "doc": "Special Collections & Study Rooms (Section 5.3)",
        "content": (
            "Quiet study carrels are available on a first-come, first-served basis on the 2nd and 3rd floors. "
            "Group study rooms can be reserved online up to 7 days in advance for sessions of up to 2 hours. "
            "Access to rare archival collections requires an appointment with the reference archivist."
        ),
        "keywords": ["room", "study", "reserve", "quiet", "space", "rare", "archive", "group", "wifi"]
    }
]

def retrieve_rag_answer(query: str):
    """
    Search relevant library documentation and formulate an answer with sources.
    Uses Gemini if GEMINI_API_KEY is configured in environment, otherwise grounded rule-based extraction.
    """
    q_lower = query.lower()
    ranked_docs = []

    for item in LIBRARY_KNOWLEDGE_BASE:
        score = 0.0
        # Keyword matches
        for kw in item["keywords"]:
            if kw in q_lower:
                score += 0.35
        # Substring/word overlap
        query_words = [w for w in q_lower.split() if len(w) > 3]
        for w in query_words:
            if w in item["content"].lower():
                score += 0.15

        if score > 0:
            confidence = min(0.98, max(0.55, score))
            ranked_docs.append((item, confidence))

    # Sort by score descending
    ranked_docs.sort(key=lambda x: x[1], reverse=True)

    # Optional Gemini Integration if API key is present
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            context_text = "\n\n".join(
                [f"Source [{doc['doc']}]: {doc['content']}" for doc, _ in ranked_docs[:3]]
            ) or "\n\n".join([f"Source [{doc['doc']}]: {doc['content']}" for doc in LIBRARY_KNOWLEDGE_BASE[:2]])
            
            prompt = (
                "You are Athenaeum, an AI assistant for the public library. "
                "Answer the user's question accurately and politely using only the provided documentation. "
                "Do not make up rules or offer account-specific transactional actions.\n\n"
                f"Documentation Context:\n{context_text}\n\n"
                f"User Question: {query}\n\nAnswer:"
            )
            response = model.generate_content(prompt)
            llm_answer = response.text.strip()
            
            top_sources = [
                SourceItem(
                    doc=doc["doc"],
                    snippet=doc["content"],
                    score=round(score, 2)
                ) for doc, score in ranked_docs[:3]
            ]
            return llm_answer, top_sources
        except Exception as e:
            # Fallback to local grounded answer if external API is unreachable
            pass

    # Built-in grounded response generator
    if ranked_docs:
        best_doc, best_score = ranked_docs[0]
        sources = [
            SourceItem(
                doc=doc["doc"],
                snippet=doc["content"],
                score=round(score, 2)
            ) for doc, score in ranked_docs[:3]
        ]
        answer = (
            f"Based on our {best_doc['doc']}: {best_doc['content']}"
        )
        return answer, sources
    else:
        # Default fallback response with general sources
        default_sources = [
            SourceItem(
                doc=LIBRARY_KNOWLEDGE_BASE[1]["doc"],
                snippet=LIBRARY_KNOWLEDGE_BASE[1]["content"],
                score=0.72
            ),
            SourceItem(
                doc=LIBRARY_KNOWLEDGE_BASE[0]["doc"],
                snippet=LIBRARY_KNOWLEDGE_BASE[0]["content"],
                score=0.68
            )
        ]
        answer = (
            "Standard cardholders may borrow up to 10 books at once for 21 days with 2 renewals. "
            "For detailed policies on membership, borrowing limits, overdue notices, or digital resources, "
            "feel free to ask a specific question."
        )
        return answer, default_sources

# Backend Contract Endpoints
@app.get("/health")
def get_health():
    """Health check endpoint required by the contract."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest):
    """Chat endpoint fulfilling the contract."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    answer, sources = retrieve_rag_answer(query)
    return ChatResponse(answer=answer, sources=sources)

# Mount static directory for static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    """Serve the single-page Athenaeum application."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
