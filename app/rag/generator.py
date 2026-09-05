"""
LLM Answer Generator module for Athenaeum.
Assembles prompt with retrieved documentation context, queries Google Gemini, and returns grounded answers.
"""

from typing import List, Dict, Any
import google.generativeai as genai

from app.config import get_gemini_api_key, GEMINI_MODEL

SYSTEM_PROMPT = """You are a Public Library Information Assistant.

Your role:
- Explain library membership rules
- Explain book borrowing procedures
- Explain overdue policies
- Explain digital library resources

Rules:
- Do NOT issue books
- Do NOT manage user accounts
- Do NOT perform transactions
- If asked to do restricted actions, politely refuse
- Answer ONLY using the provided context below. If the context does not contain the answer, say you don't have that information rather than guessing.

Respond in a clear, friendly, and simple manner."""

NO_CONTEXT_MESSAGE = "I don't have information about that in the library's documentation."

def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Generate a grounded library answer using Google Gemini.
    Skips API call if retrieved_chunks is empty to prevent hallucination and conserve quota.
    """
    # Empty-context check: if no chunks passed MIN_SIMILARITY
    if not retrieved_chunks:
        return NO_CONTEXT_MESSAGE

    # Assemble formatted context block
    context_blocks = []
    for chunk in retrieved_chunks:
        source_file = chunk.get("source_file", "library-docs")
        section = chunk.get("section", "General")
        text = chunk.get("text", "").strip()
        context_blocks.append(f"[Source: {source_file} — {section}]\n{text}")

    context_str = "\n\n".join(context_blocks)

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context_str}\n\n"
        f"User Question: {query}\n\n"
        f"Answer:"
    )

    # Configure Gemini API
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(full_prompt)

    if response and hasattr(response, "text") and response.text:
        return response.text.strip()
    return "I was unable to formulate a response based on the library records."
