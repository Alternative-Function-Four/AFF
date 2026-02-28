Project: AFF monorepo scaffold for a proactive local activity suggestion assistant (Activity Assistant SpecKit). Current implemented slice is a FastAPI backend in `services/api` with public/admin routes, in-memory state, event/feed generation, feedback, and source ingestion workflow.

Tech stack:
- Python 3.11
- FastAPI
- Pydantic
- pytest
- Ruff + pyrefly for lint/type checks
- UV as package/venv/task runner

Rough structure:
- `services/api/`: app source + tests
- `docs/spec/`: product/architecture/API/ops/acceptance spec pack (docs-only)
- `.specify/`: spec-kit artifacts
- `.github/workflows/ci.yml`: CI checks (Ruff + pyrefly)
- `Makefile`: run/test entry aliases
- `.agents/`: agent-specific skill docs and system files