# NOESIS Backend Developer Guide

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (mostly optional for public repos)
```

### 4. Start Server

```bash
python main.py
# or with auto-reload:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

## API Endpoints

### POST /api/analyze
Initiate analysis.

**Request:**
```json
{ "repo_url": "https://github.com/owner/repo" }
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

### GET /api/analyze/{session_id}/progress
Stream progress and logs.

**Response:**
```json
{
  "session_id": "uuid",
  "status": "running",
  "progress": 42,
  "stage": "Analyzing structure",
  "log_lines": [
    {
      "timestamp": "2025-05-17T...",
      "level": "info",
      "message": "..."
    }
  ]
}
```

### GET /api/analyze/{session_id}/result
Fetch completed analysis (202 if still processing).

**Response:** AnalysisResult object

### GET /api/health
Health check for load balancers.

## Architecture

### Core Modules

- **main.py**: FastAPI app, routes, session management
- **github_service.py**: GitHub API client, repository snapshot
- **analysis_engine.py**: Heuristic-based architectural analysis
- **bob_service.py**: Bob pipeline orchestration (ready for SDK integration)
- **risk_engine.py**: Scoring logic and breakdown calculation
- **schemas.py**: Pydantic data models

### Analysis Pipeline

1. **GitHub Fetch** (0-25%): Clone repo metadata via GitHub API
2. **Structure Analysis** (25-40%): Detect components, entry points, critical files
3. **Architectural Reasoning** (40-90%): Map data flows, identify risks, score files
4. **Report Generation** (90-100%): Finalize JSON export, create audit log

### Data Flow

```
POST /api/analyze
  ↓ (async background task)
├→ fetch_repo_snapshot() → GitHub API
├→ AnalysisEngine().run_analysis() → heuristics
├→ calculate_score_breakdown() → 5-factor scores
├→ compute_exploitability_score() → 0-100
├→ BobSession.export_to_file() → bob-exports/{uuid}.json
└→ Session stored in memory (ready for polling)

GET /api/analyze/{session_id}/progress
  ↓
Session state from in-memory dict

GET /api/analyze/{session_id}/result
  ↓ (when status = COMPLETED)
AnalysisResult from session.result
```

## Testing

### Manual Tests

```bash
# 1. Start backend
python main.py

# 2. In another terminal, initiate analysis
RESPONSE=$(curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/torvalds/linux"}')

SESSION_ID=$(echo $RESPONSE | jq -r .session_id)

# 3. Poll progress
curl http://localhost:8000/api/analyze/$SESSION_ID/progress

# 4. Fetch result (after progress = 100)
curl http://localhost:8000/api/analyze/$SESSION_ID/result
```

### Log Inspection

Analysis logs are written to `bob-exports/` as JSON files:
- File naming: `bob_export_{repo}_{timestamp}.json`
- Contains: metadata, conversation history, analysis results
- Used for audit trail and re-evaluation

## IBM Bob Integration

### Current State
- `AnalysisEngine` provides heuristic-based analysis
- `BobSession` class ready for SDK integration
- Mock exports created in `bob-exports/` for demo

### When Bob SDK Available
1. Get API credentials from IBM
2. Update `.env`:
   ```
   BOB_API_KEY=your-key
   BOB_API_ENDPOINT=your-endpoint
   ```
3. In `bob_service.py`, replace `AnalysisEngine` calls with:
   ```python
   from ibm_bob import IBMBob
   bob = IBMBob(api_key=os.getenv('BOB_API_KEY'), ...)
   response = bob.prompt(message, context=repo_snapshot)
   ```

## Production Deployment

### Requirements
- Redis or PostgreSQL for session persistence
- GitHub token for higher rate limits
- Bob SDK credentials
- CORS configuration update

### Deployment Steps

```bash
# Build
pip install -r requirements.txt

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app

# Or with systemd (see deployment guide)
```

### Environment Variables
- `ENV=production`
- `HOST=0.0.0.0`
- `PORT=8000`
- `GITHUB_TOKEN=your-token` (recommended)
- `BOB_API_KEY=your-key`
- `BACKEND_URL=https://your-domain/api`

## Troubleshooting

### GitHub API Rate Limiting
- Add `GITHUB_TOKEN` to `.env` (increases from 60/hr to 5000/hr)
- Get token: https://github.com/settings/tokens

### Session Not Found
- Check session ID is valid UUID
- Ensure backend hasn't been restarted (in-memory storage)
- Use PostgreSQL for production persistence

### Analysis Hangs
- Check logs in `/tmp` or stdout
- Verify network connectivity to GitHub
- Increase timeout in `github_service.py` if needed

## Performance Tuning

- **Concurrency**: Update FastAPI `workers` for better throughput
- **Caching**: Add Redis for session persistence across restarts
- **GitHub Fetching**: Consider caching file trees for frequently analyzed repos
- **Async I/O**: All I/O operations are async-compatible

---

**Questions?** Check `README.md` or create an issue.
