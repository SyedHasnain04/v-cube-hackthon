# Athenaeum — RAG Library Assistant

**Athenaeum** is an end-to-end Retrieval-Augmented Generation (RAG) assistant designed to explain public library services (membership rules, borrowing procedures, overdue policies, and digital resources) grounded strictly in library documentation.

---

## 🏛 Architecture & Tech Stack

- **Frontend**: Plain HTML5, Vanilla CSS, and Vanilla JavaScript (zero framework, zero build step) located in `static/`.
  - Dimmed cinematic looping video background.
  - Liquid glassmorphic panels (`.liquid-glass`) with luminosity blend-mode and gradient borders.
  - Google Fonts pairing (*Instrument Serif* & *Inter*).
  - Collapsible source citations and live status heartbeat.
- **Backend Framework**: **FastAPI** + **Uvicorn** serving both API endpoints and the static UI.
- **Embeddings**: `sentence-transformers` using `all-MiniLM-L6-v2` (local, fast, free, no external API calls).
- **Vector Index**: **FAISS** (`IndexFlatIP` with L2-normalized vectors for exact cosine similarity).
- **LLM Synthesis**: **Google Gemini** (`gemini-2.5-flash`) via `google.generativeai`.
- **Secrets Management**: `python-dotenv` loading `GEMINI_API_KEY` from `.env`.

---

## 📂 Project Structure

```text
v-cube-hackthon/
├── app/
│   ├── main.py              # FastAPI app, routes, CORS, and static file mount
│   ├── config.py            # Environment loading & pipeline constants
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py        # Markdown/text loading, header-based chunking, FAISS builder
│   │   ├── retriever.py     # Embedding query & FAISS top-k similarity search
│   │   └── generator.py     # Prompt assembly with guardrails & Gemini answer generation
│   └── data/
│       ├── docs/            # Library policy documents (.md / .txt)
│       └── index/           # faiss.index & chunks.json (generated, gitignored)
├── static/
│   ├── index.html           # Single-page interface with video background & layout
│   ├── style.css            # Dark navy theme, liquid glass effect, responsive styles
│   └── script.js            # Frontend logic for API calls, health check & UI rendering
├── .env.example             # Template for GEMINI_API_KEY
├── .gitignore
├── requirements.txt         # Backend Python dependencies
└── README.md
```

---

## 📡 API Contract

| Method | Endpoint | Description | Payload / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root interface | Serves `static/index.html` |
| `GET` | `/health` | Health check | `{ "status": "ok" }` |
| `POST` | `/chat` | RAG query | **Body:** `{ "query": "string" }`<br>**Response:** `{ "answer": "string", "sources": [{ "doc": "...", "snippet": "...", "score": 0.95 }] }` |
| `POST` | `/ingest` | Index rebuild | `{ "status": "ok", "chunks_indexed": 12 }` |
| `GET` | `/static/*` | Static assets | Serves `index.html`, `style.css`, `script.js` |

---

## 🚀 Local Development Setup

### 1. Configure Environment
Copy `.env.example` to `.env` and insert your Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Ingest Policy Documents
To build or rebuild the FAISS vector index from `app/data/docs/`:
```bash
python -m app.rag.ingest
```

### 4. Run the Server
```bash
uvicorn app.main:app --reload --port 8000
```

Access the interface at: `http://localhost:8000`.