# NOESIS — Nested Orchestration of Exploitability & Structure Insight System

**Enterprise-grade repository security intelligence through architectural analysis.**

NOESIS is a full-stack application that accepts a GitHub repository URL and delivers a security-focused architectural report. Rather than traditional line-level scanning, NOESIS reasons across the repository structure to identify privilege boundaries, data flow risks, and entry point exposure—then prioritizes remediation with actionable refactor suggestions.

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

**Environment variables:**
- `BACKEND_URL` (optional): Backend API endpoint (defaults to `http://localhost:8000`)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cd ..
python -m backend.main
```

Server runs on `http://localhost:8000`.

---

## Features

### Landing Page
- Clean, terminal-style entry point
- Repository URL validation
- Recent analysis session history with scores

### Analysis Loading
- Real-time progress tracking (0–100%)
- Staged analysis pipeline visible:
  - Cloning repository
  - Resolving dependency graph
  - Mapping entry points
  - Tracing data flows
  - Checking privilege boundaries
  - Scoring risk
  - Finalizing report
- Live execution log (color-coded by severity)

### Dashboard
- **Exploitability Score**: Large, color-coded numeric score (0–100)
- **Risk Breakdown**: Heatmap of risk factors (authentication, authorization, input validation, data exposure, dependencies)
- **Architecture Topology**: Module-level risk map with files affected
- **Entry Points**: HTTP routes, CLI endpoints, auth requirements, per-endpoint risk
- **Data Flows**: Input-to-storage traces with validation status
- **Privilege Violations**: Cross-module authorization gaps with rationale
- **Refactor Intelligence**: Prioritized, actionable fixes with code snippets and effort estimates
- **File Risk Index**: Sortable list of risky files with specific issues and severity

---

## Architecture

### Frontend Stack
- **Next.js 14** (React framework)
- **Tailwind CSS** (dark theme, monospace typography, custom spacing)
- **Client-side state management** via `useState` and `sessionStorage`

### Backend Stack
- **FastAPI** (Python web framework)
- **GitHub REST API** (repository ingestion)
- **IBM Bob** (architectural reasoning and analysis)

### Data Flow
1. User submits repository URL on landing page.
2. Frontend navigates to loading page, shows animated progress.
3. Backend receives analysis request, clones repo, runs structured Bob prompts, scores results.
4. Frontend polls `/api/analysis/:sessionId` endpoint for progress and results.
5. On completion, dashboard displays full security intelligence report.

---

## API Endpoints

### POST `/api/analysis`
Start a new analysis session.

**Request:**
```json
{ "repo_url": "https://github.com/organization/repository" }
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "repo_url": "...",
  "status": "queued",
  "created_at": "2025-05-17T..."
}
```

### GET `/api/analysis/:sessionId/status`
Poll for progress.

**Response:**
```json
{
  "session_id": "uuid",
  "status": "running",
  "progress": 42,
  "stage": "Tracing data flows",
  "log_lines": [...]
}
```

### GET `/api/analysis/:sessionId/result`
Retrieve completed analysis.

**Response:**
```json
{
  "session_id": "uuid",
  "repo_url": "...",
  "score": 72,
  "score_breakdown": {...},
  "architecture": [...],
  "entry_points": [...],
  "data_flows": [...],
  "privilege_issues": [...],
  "suggestions": [...],
  "file_risks": [...]
}
```

---

## Project Structure

```
NOESIS/
├── frontend/              # Next.js frontend
│   ├── pages/             # Route pages (index, loading, dashboard)
│   ├── components/        # UI components (ScoreCard, Heatmap, etc.)
│   ├── lib/               # Utilities and sample fallback data
│   ├── styles/            # Global CSS
│   ├── package.json
│   └── tsconfig.json
├── backend/               # FastAPI backend
│   ├── main.py            # App entry point
│   ├── github_service.py  # GitHub REST API client
│   ├── bob_service.py     # Bob orchestration
│   ├── risk_engine.py     # Risk scoring
│   ├── prompt_templates.py # Bob prompt definitions
│   ├── schemas.py         # Pydantic models
│   └── requirements.txt
├── bob-exports/           # Exported Bob session logs (JSON)
├── docs/                  # Documentation
├── .gitignore
└── README.md
```

---

## Scoring Methodology

The **Exploitability Score** (0–100) is a weighted composite of risk factors:

- **Authentication Risk**: Missing or inconsistent auth decorators
- **Authorization Risk**: Privilege boundary violations
- **Input Validation Risk**: Unvalidated data flows to critical sinks
- **Data Exposure Risk**: Sensitive data handling gaps
- **Dependency Risk**: Vulnerable or outdated packages

Each factor is normalized to 0–100, then aggregated with weights. A score of 80+ indicates **critical risk**, 60–79 = **high**, 40–59 = **elevated**, <40 = **acceptable**.

---

## Bob Integration

NOESIS leverages **IBM Bob** for architectural reasoning:

1. **Repository snapshot** — fetches file tree via GitHub REST API
2. **Structured prompts** — asks Bob to:
   - Map architecture and module responsibilities
   - Identify entry points and external interfaces
   - Trace data flows from input to storage
   - Flag privilege boundary violations
   - Summarize risks and suggest refactors
3. **Session export** — saves Bob conversation and structured JSON to `bob-exports/`

Each Bob session is timestamped and archived for audit and future re-analysis.

### Run With Local Bob Installed

1. Edit [backend/.env.example](backend/.env.example) into a local .env for backend.
2. Set Bob mode to CLI and provide the exact command that reads prompt text from stdin and prints JSON.
3. Start backend and run analysis from frontend.

Recommended environment values:
- BOB_MODE=cli
- BOB_CLI_COMMAND=<your bob command>

If your Bob installation exposes HTTP instead of CLI:
- BOB_MODE=http
- BOB_API_ENDPOINT=<your Bob endpoint>
- BOB_API_KEY=<your key if required>

---

## Development

### Running Tests (Frontend)
```bash
cd frontend
npm run lint
npm run build
```

### Adding a New Component
1. Create file in `frontend/components/`
2. Export a named function component
3. Import in relevant page and wire props from `result` object

### Extending Backend
1. Add routes to `backend/main.py`
2. Add Pydantic schemas to `schemas.py`
3. Test locally: `curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" -d '{"repo_url":"..."}'`

---

## Deployment

### Frontend (Vercel recommended)
```bash
vercel deploy
# Set BACKEND_URL environment variable in Vercel project settings
```

### Backend (Any Node/Python host)
```bash
# Railway, Render, Heroku, etc.
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
```

---

## Known Limitations & Future Work

- **Sample analysis fallback**: If the backend is unavailable, the frontend shows deterministic sample data.
- **No GitHub authentication**: Public repos only; private repos require GitHub token.
- **Dependency scanning**: Currently partial; extend with SBOM parsing (CycloneDX, SPDX).
- **Database persistence**: Sessions are in-memory; add PostgreSQL/MongoDB for production.
- **Real-time collaboration**: Single-user for now; can add WebSocket for live team reviews.

---

## License

See `LICENSE` file.

---

## Questions?

For issues, open a GitHub issue or contact the maintainers.

**Built with ❤️ for security-conscious development teams.**
