# NOESIS Releases & Data Re-evaluation Policy

This document describes the release process, how past analysis sessions are re-evaluated, and how historical data is preserved.

---

## Release Schedule

NOESIS follows a **semantic versioning** scheme: `MAJOR.MINOR.PATCH`

- **MAJOR**: Architectural changes or breaking API changes
- **MINOR**: New features, new scoring factors, improved analysis depth
- **PATCH**: Bug fixes, performance improvements, UI refinements

### Current Version
- **v0.1.0** (Initial release for IBM competition)

### Upcoming Milestones
- **v0.2.0** — Real IBM Bob integration (currently uses mock analysis)
- **v0.3.0** — Database persistence (PostgreSQL) for session history
- **v0.4.0** — Private repository support (GitHub token integration)
- **v1.0.0** — Production-ready with team collaboration features

---

## Data Re-evaluation Strategy

### When Are Past Sessions Re-evaluated?

Past analysis sessions are **not automatically re-run** but can be re-evaluated in these scenarios:

1. **Scoring Algorithm Update**
   - If the exploitability score weights change (e.g., doubling authorization risk factor), historical scores are recomputed on-demand.
   - The original Bob analysis data is preserved; only the numerical score is recalculated.
   - Example: If you update `risk_engine.py` to change weights, calling `GET /api/analysis/:sessionId/result` will return the new score.

2. **New Scoring Factors Introduced**
   - If a new risk category is added (e.g., "API rate limiting enforcement"), re-evaluation includes the new factor for all past sessions.
   - Sessions are backfilled with default or interpolated values for the new factor.

3. **Bug Fixes in Analysis Logic**
   - If a bug is discovered in privilege boundary detection, re-evaluation re-runs the corrected logic on the stored repository snapshot.
   - The original Bob export is never modified; corrections create a new analysis record.

4. **Manual Re-analysis Request**
   - Users can explicitly re-analyze a repository URL to refresh insights.
   - The new session gets a new `session_id` and is stored alongside historical results.

### How Data Is Preserved

- **Bob Session Exports**: Every analysis generates a timestamped JSON export in `bob-exports/` containing:
  - Metadata (repo URL, timestamp, session ID)
  - Full Bob conversation history
  - Structured JSON output (architecture, data flows, suggestions)
  - Raw scores at time of analysis
  
- **Immutable Archive**: Once saved, Bob exports are read-only. They serve as audit trail and enable offline re-scoring.

- **Session Metadata**: Stores:
  - Analysis start and end times
  - Repository snapshot (file tree, entry points detected)
  - User/environment info (for enterprise deployments)
  - Release version when analysis was run

### Example: Scoring Algorithm Change

**Scenario:** Initial release uses `[auth: 2x, authz: 3x, input: 4x, exposure: 2x, deps: 2x]` weights.

**New release v0.2.1:** Research shows authorization is even more critical; weights updated to `[auth: 2x, authz: 5x, input: 4x, exposure: 2x, deps: 2x]`.

**Effect on past sessions:**
- Bob exports remain unchanged (immutable)
- If you call `GET /api/analysis/session-123/result`, the score is recalculated with new weights
- Original score is preserved in the Bob export for comparison
- Frontend can show both "score at time of analysis" and "current score" if desired

---

## Release Checklist

Before each release:

- [ ] Update version in `frontend/package.json` and `backend/main.py`
- [ ] Run frontend build: `npm run build`
- [ ] Run backend tests: `pytest tests/` (if tests exist)
- [ ] Update `RELEASES.md` with new entries
- [ ] Tag commit: `git tag v0.X.Y`
- [ ] Document any breaking changes in `MIGRATION.md` (if applicable)
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to hosting provider
- [ ] Test end-to-end flow in production

---

## Version History

### v0.1.0 (May 17, 2026)
**Initial Release**

- Landing page with repository URL input
- Analysis loading page with live progress visualization
- Security dashboard with:
  - Exploitability score (0–100)
  - Risk heatmap by category
  - Architecture topology map
  - Entry point listing
  - Data flow tracing
  - Privilege violation detection
  - Refactor suggestions with code snippets
  - File risk index
- FastAPI backend with mock analysis engine
- GitHub repository ingestion
- Bob prompt templates (ready for integration)
- Bob session export to `bob-exports/`
- Next.js + Tailwind CSS frontend
- TypeScript throughout

**Known Limitations:**
- Mock analysis (IBM Bob not live-wired yet)
- In-memory session storage (no database)
- Public repositories only

---

## Migration Guide

### Upgrading from v0.1.0 to v0.2.0 (Planned)

**Breaking Changes:**
- `/api/analysis` response will include `bob_transcript` field (new)
- `score_breakdown` keys may be renamed to match Bob's output schema

**Migration Steps:**
1. Backup existing `bob-exports/` directory
2. Pull latest frontend and backend code
3. Run frontend build: `npm run build`
4. Restart backend server
5. New analyses will use real Bob reasoning
6. Existing mock analyses are still retrievable

---

## Data Retention Policy

- **Bob Exports**: Kept indefinitely in `bob-exports/`
- **Session Metadata**: 90 days (configurable)
- **Analysis Logs**: 30 days (configurable)
- **User Data**: Deleted on request (GDPR compliance)

---

## Support & Questions

- Report bugs: Create an issue with steps to reproduce
- Request features: Describe use case and desired behavior
- Data re-evaluation questions: Contact maintainers

---

## Contributing

We welcome contributions! To propose changes to scoring logic or analysis methodology:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/improved-scoring`
3. Make changes and test locally
4. Submit a pull request with:
   - Description of change
   - Impact on past/future scores
   - Any migration concerns
   - Test results

---

**Last Updated:** May 17, 2026

**Current Status:** v0.1.0 (Pre-release)
