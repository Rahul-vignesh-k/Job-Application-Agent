# JobAgent AI — Automated Job Application Agent

A full-stack AI-powered job application agent that discovers, analyses, tailors, and submits job applications automatically using **Gemini**, **ChromaDB RAG**, **Playwright**, and **MCP connectors**.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS + shadcn UI |
| Backend | FastAPI + Python 3.12 |
| Database | SQLite (via SQLAlchemy async) |
| Vector DB | ChromaDB |
| AI | Gemini 1.5 Pro |
| Automation | Playwright (async) |
| Containers | Docker + docker-compose |

---

## Features

- **Job Discovery** — scrapes LinkedIn, Naukri, Indeed, Glassdoor (MCP stubs included, real Playwright scrapers ready to implement)
- **Match Analysis** — Gemini + ChromaDB RAG compares your resume vs every JD; returns score, matched/missing skills, gap analysis
- **Auto-Apply** — jobs with match score ≥ 85% are applied to automatically
- **Smart Tailoring** — jobs below threshold show gaps in UI, offer AI-tailored resume with approval flow
- **Manual Input** — unknown form fields pause automation and surface in UI for one-time answers, saved to SQLite + ChromaDB for reuse
- **Smart Answer Lookup** — before asking, checks `.env → SQLite → ChromaDB` in priority order
- **Full Audit Trail** — every job, score, status, resume version, application result, and agent log persisted

---

## Quick Start

### 1. Prerequisites
- Python 3.12+
- Node 20+
- Docker (optional)

### 2. Configure
```bash
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY
```

### 3. Backend
```bash
pip install -r requirements.txt
playwright install chromium

# From project root:
uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 5. Docker (production)
```bash
docker-compose up --build
# → http://localhost:8000  (serves built frontend + API)
```

---

## Project Structure

```
project_rag/
├── backend/
│   ├── main.py              # FastAPI app + CORS + lifespan
│   ├── config.py            # Pydantic settings (from .env)
│   ├── db/
│   │   ├── database.py      # SQLAlchemy async engine
│   │   ├── models.py        # Job, Resume, Application, SavedAnswer, …
│   │   └── crud.py          # CRUD helpers
│   ├── agent/
│   │   ├── state_machine.py # States + transitions
│   │   └── job_agent.py     # Orchestration logic
│   ├── mcp/
│   │   ├── base.py          # BaseConnector ABC
│   │   ├── linkedin.py      # LinkedIn connector (stub → Playwright)
│   │   ├── naukri.py        # Naukri connector stub
│   │   ├── indeed.py        # Indeed connector stub
│   │   └── glassdoor.py     # Glassdoor connector stub
│   ├── rag/
│   │   ├── chromadb_client.py  # ChromaDB singleton + helpers
│   │   └── matcher.py          # Gemini match + tailor prompts
│   ├── automation/
│   │   └── applicator.py    # Playwright form automation
│   ├── resumes/
│   │   └── resume_processor.py  # PDF/DOCX extraction + chunking
│   └── api/
│       ├── jobs.py          # /api/jobs endpoints
│       ├── resumes.py       # /api/resumes endpoints
│       ├── answers.py       # /api/answers endpoints
│       ├── history.py       # /api/history endpoints
│       └── settings_api.py  # /api/settings endpoints
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, JobQueue, JobDetail, MatchReport,
│       │                    # ResumePreview, ManualInput, History, Settings
│       ├── components/      # JobCard, ScoreRing, StatCard, shadcn UI
│       ├── lib/             # api.ts (Axios), utils.ts
│       └── types/index.ts   # TypeScript types
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/jobs | List all jobs (filterable) |
| POST | /api/jobs/discover | Scrape jobs from platforms |
| GET | /api/jobs/stats | Status breakdown counts |
| GET | /api/jobs/:id | Job detail |
| POST | /api/jobs/:id/analyse | Run Gemini match analysis |
| POST | /api/jobs/:id/tailor | Generate tailored resume |
| POST | /api/jobs/:id/apply | Submit application via Playwright |
| POST | /api/jobs/:id/resolve-fields | Provide answers for unknown fields |
| POST | /api/resumes/upload | Upload PDF/DOCX resume |
| GET | /api/answers | List saved form answers |
| POST | /api/answers | Save/update an answer |
| GET | /api/history/applications | Application history |
| GET | /api/history/logs | Agent event log |
| GET | /api/settings | Get current settings |
| PATCH | /api/settings | Update settings |

---

## State Machine

```
DISCOVERED → ANALYZING → MATCHED (≥85%) → APPLYING → APPLIED
                       ↘ REVIEW_REQUIRED → TAILORING → READY_TO_APPLY → APPLYING
                                         ↘ SKIPPED
                                                         ↘ WAITING_INPUT → APPLYING
```

---

## Extending Real Scrapers

Each connector in `backend/mcp/` inherits `BaseConnector`. Replace the stub `search()` and `get_details()` methods with Playwright code:

```python
async def search(self, keywords, location="", limit=20):
    await self._ensure_browser()
    await self._login()
    # ... real scraping logic
    return [RawJob(...)]
```

---

## License
MIT
