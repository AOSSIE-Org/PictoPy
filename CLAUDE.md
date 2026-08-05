# CLAUDE.md

@AGENTS.md

## Claude Code

Area-specific rules load automatically from the nearest `AGENTS.md` when you read a file in
`backend/`, `frontend/`, `frontend/src-tauri/`, or `sync-microservice/`.

Reusable playbooks live in `agent-kit/` — see `agent-kit/README.md` for the index.

Available skills:

- `/onboard` — first-time setup and repo tour
- `/add-backend-endpoint` — scaffold a FastAPI endpoint end to end
- `/add-frontend-feature` — scaffold a slice, API wrapper, hook, component, and test
- `/pre-pr-check` — run every gate CI runs, before pushing

Use plan mode for changes touching `backend/app/database/` (schema changes ripple into
`main.py`, `conftest.py`, and the sync microservice) or `frontend/src-tauri/`.
