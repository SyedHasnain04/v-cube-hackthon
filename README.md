# Athenaeum — RAG Library Assistant

An intelligent, single-page RAG chat interface called **"Athenaeum"** featuring a dimmed looping cinematic background video, liquid glassmorphism, and typography designed for library documentation lookup.

Built with **plain HTML, Vanilla CSS, and Vanilla JavaScript** on the frontend, served by a **FastAPI** backend conforming to the RAG API specification.

---

## 🏛 Features

- **Cinematic Atmospheric Video Background**: Looping library video dimmed with an overlay (`rgba(6, 20, 33, 0.82)`) preserving text contrast and readability.
- **Liquid Glassmorphism**: Custom CSS glass panels with dynamic light refraction and multi-layer backdrop blur.
- **Google Fonts Typography**: *Instrument Serif* for headings and *Inter* for interface readability.
- **Live Health Indicator**: Real-time heartbeat checking `/health` endpoint to display online/offline status in the navigation bar.
- **Collapsible Grounded Sources**: Expandable glass cards with relevance percentage badges, document titles, and truncated text snippets.
- **Zero-Dependency Frontend**: Pure HTML/CSS/JS without frameworks, npm dependencies, or build steps.
- **FastAPI Backend**: Implements `/health`, `POST /chat`, and serves static assets.

---

## 📡 Backend API Contract

| Method | Endpoint | Description | Payload / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health check | `{ "status": "ok" }` |
| `POST` | `/chat` | RAG query | **Body:** `{ "query": "string" }`<br>**Response:** `{ "answer": "string", "sources": [{ "doc": "...", "snippet": "...", "score": 0.95 }] }` |
| `GET` | `/static/*` | Static assets | Serves `index.html`, `style.css`, `script.js` |

---

## 🚀 Local Quickstart

### 1. Prerequisites
- Python 3.9+ installed
- Git

### 2. Setup & Run
```bash
# Clone the repository
git clone https://github.com/SyedHasnain04/v-cube-hackthon.git
cd v-cube-hackthon

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set Gemini API Key for dynamic LLM generation
# set GEMINI_API_KEY="your-gemini-api-key"

# Start the server
uvicorn main:app --reload --port 8000
```

Open your browser at `http://localhost:8000`.

---

## ☁️ Deployment Guides

### Option 1: Deploy on Render (Recommended Free & Fast)
1. Push your repository to GitHub.
2. Go to [Render.com](https://render.com) and create a **New Web Service**.
3. Connect your `v-cube-hackthon` repository.
4. Configure settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. (Optional) In **Environment Variables**, add `GEMINI_API_KEY` if using Google AI Studio.
6. Click **Deploy Web Service**.

---

### Option 2: Deploy on Railway
1. Go to [Railway.app](https://railway.app) and click **New Project** → **Deploy from GitHub repo**.
2. Select your repository.
3. Railway automatically detects `requirements.txt` and starts Uvicorn.
4. If needed, configure start command:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Click **Deploy**.

---

### Option 3: Deploy with Docker
Create a `Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build & run:
```bash
docker build -t athenaeum-rag .
docker run -p 8000:8000 athenaeum-rag
```

---

## 📂 Project Structure

```text
v-cube-hackthon/
├── main.py              # FastAPI application, RAG logic & static file serving
├── requirements.txt     # Backend dependencies
├── README.md            # Documentation & deployment instructions
└── static/
    ├── index.html       # Single-page app with video background & glass layout
    ├── style.css        # CSS variables, liquid glass effect, responsive design
    └── script.js        # Vanilla JS for API requests, health check & UI rendering
```