# Athenaeum — RAG Library Assistant

**Athenaeum** is an end-to-end Retrieval-Augmented Generation (RAG) assistant designed to explain public library services (membership rules, borrowing procedures, overdue policies, and digital resources) grounded strictly in library documentation.

---

## 🏛 Architecture & Tech Stack

- **Frontend**: Plain HTML5, Vanilla CSS, and Vanilla JavaScript (zero framework, zero build step) located in `static/` and `index.html`.
  - Dimmed cinematic looping video background.
  - Liquid glassmorphic panels (`.liquid-glass`) with luminosity blend-mode and gradient borders.
  - Google Fonts pairing (*Instrument Serif* & *Inter*).
  - Quick-start suggestion chips, collapsible source citations, and live status heartbeat.
- **Backend Framework**: **FastAPI** + **Uvicorn** serving both API endpoints and the static UI.
- **Embeddings**: `sentence-transformers` using `all-MiniLM-L6-v2` (local, fast, free, no external API calls).
- **Vector Index**: **FAISS** (`IndexFlatIP` with L2-normalized vectors for exact cosine similarity).
- **LLM Synthesis**: **Google Gemini** (`gemini-2.5-flash`) via `google.generativeai`.
- **Secrets Management**: `python-dotenv` loading `GEMINI_API_KEY` from `.env`.

---

## ❓ Questions You Can Ask Athenaeum

Athenaeum is grounded in library documentation. Here are sample questions organized by topic:

### 💳 Library Membership & Registration
- *"How do I register for a library card and what documents are required?"*
- *"Can non-residents apply for a library card?"*
- *"What are the membership rules for youth or students under 18?"*
- *"How do educators qualify for extended borrowing privileges?"*
- *"What should I do if my library card is lost or stolen?"*

### 📚 Borrowing Limits, Loan Periods & Renewals
- *"How many books can I borrow at once?"*
- *"What is the loan period for DVDs and new release bestsellers?"*
- *"How many times can I renew borrowed items?"*
- *"Do books renew automatically?"*
- *"How many hold requests can I place simultaneously?"*

### ⏳ Overdue Policies, Fines & Replacement Fees
- *"Are there late fines for returning books overdue?"*
- *"What happens if an item is overdue for more than 30 days?"*
- *"Can a lost item replacement fee be waived if I find and return the book?"*
- *"When are overdue notices and courtesy reminders sent out?"*

### 📱 Digital E-Books, Audiobooks & Database Access
- *"How do I access digital e-books and audiobooks on Libby / OverDrive?"*
- *"How many movie streaming credits do I receive on Hoopla and Kanopy each month?"*
- *"How do I log in to JSTOR and academic research databases from home?"*
- *"What is my default PIN for digital service authentication?"*

---

## ⚡ Handling Render Free-Tier Cold Starts

Render's free tier spins down after 15 minutes of inactivity. To ensure visitors never wait for cold starts:

1. **Free External Pinger (Recommended — No Code / No Vercel Crons)**:
   - Go to [cron-job.org](https://cron-job.org) or [uptimerobot.com](https://uptimerobot.com) (both 100% free).
   - Create an HTTP monitor pointing to:
     ```
     https://athenaeum-rag.onrender.com/health
     ```
   - Set the interval to **every 10 minutes**.
   - This keeps your Render container warm 24/7 without needing any cron configurations in Vercel or code in your repo.

2. **Proactive Frontend Wake-Up (In-App)**:
   - When a user opens your Vercel URL, the frontend immediately sends a background ping to `/health`, triggering the wake-up process before the user finishes typing.
   - The status indicator in the top navbar clearly shows `"Waking engine…"` with a pulsing dot so the user is informed.

3. **Transparent Progressive Loading Indicator**:
   - If a question is asked while the engine is waking up, the UI shows real-time progress:
     - *0–5s*: `"Athenaeum is thinking…"`
     - *6–20s*: `"Waking library engine from sleep… (~25s)"`
     - *20s+*: `"Formulating grounded answer from library records…"`

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
├── index.html               # Root entry for Vercel zero-config static hosting
├── vercel.json              # Vercel rewrite configuration to Render backend
├── render.yaml              # Render 1-click blueprint specification
├── .env.example             # Template for GEMINI_API_KEY
├── .gitignore
├── requirements.txt         # Backend Python dependencies
└── README.md
```

---

## 📡 API Contract

| Method | Endpoint | Description | Payload / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root interface | Serves `index.html` |
| `GET` | `/health` | Health check | `{ "status": "ok" }` |
| `POST` | `/chat` | RAG query | **Body:** `{ "query": "string" }`<br>**Response:** `{ "answer": "string", "sources": [{ "doc": "...", "snippet": "...", "score": 0.95 }] }` |
| `POST` | `/ingest` | Index rebuild | `{ "status": "ok", "chunks_indexed": 12 }` |
| `GET` | `/static/*` | Static assets | Serves `style.css`, `script.js` |

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