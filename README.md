# Athenaeum — RAG Library Assistant UI

A single-page RAG chat interface called **"Athenaeum"** featuring a dimmed looping cinematic background video, liquid glassmorphic panels, and typography designed for library documentation queries.

Built with **plain HTML, Vanilla CSS, and Vanilla JavaScript** (no framework, no build step) to be served as static files by a backend (e.g., FastAPI).

---

## 🏛 UI Features & Design System

- **Atmospheric Video Background**: Fullscreen looping library video muted and dimmed with a dark overlay (`rgba(6, 20, 33, 0.82)`) ensuring chat readability.
- **Liquid Glass Effect (`.liquid-glass`)**: Glass panels with multi-layer backdrop blur, luminosity blend-mode, and top/bottom gradient borders.
- **Typography**: Google Fonts pairing — **Instrument Serif** for display/headings and **Inter** (weights 400/500) for body and UI elements.
- **Color Theme**: Dark navy palette utilizing HSL CSS variables (`--background: 201 100% 13%`, `--foreground: 0 0% 100%`, etc.).
- **Live Health Status**: Real-time heartbeat checking the `/health` endpoint to reflect status in the navigation bar pill.
- **Collapsible Grounded Sources**: Expandable glass cards under assistant messages displaying document name, percentage match badge, and truncated snippets.
- **Micro-Animations**: Staggered `animate-fade-rise` animations on initial hero elements and each newly inserted chat message.
- **Pure Zero-Dependency Frontend**: 100% standard web technologies — no React, Vite, Tailwind, or icon libraries.

---

## 📡 Expected Backend Contract

The UI communicates with the backend using the following standard endpoints:

| Method | Endpoint | Description | Payload / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Live health check | `{ "status": "ok" }` |
| `POST` | `/chat` | RAG query | **Body:** `{ "query": "string" }`<br>**Response:** `{ "answer": "string", "sources": [{ "doc": "...", "snippet": "...", "score": 0.95 }] }` |
| `GET` | `/static/*` | Static files | Serves `index.html`, `style.css`, `script.js` |

---

## 📂 Project Structure

```text
v-cube-hackthon/
├── README.md            # Documentation & contract specifications
└── static/
    ├── index.html       # Single-page interface with video background & layout
    ├── style.css        # CSS variables, liquid glass effect, responsive design
    └── script.js        # Vanilla JS for API requests, health check & UI rendering
```