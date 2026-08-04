# AGENTS.md — sync microservice

Rules for the filesystem sync service. The root `AGENTS.md` still applies.

This is a **separate FastAPI service** from `backend/`, with its own `requirements.txt`,
its own virtualenv, and its own PyInstaller build (`PictoPy_Sync_Microservice`). It watches
folders registered in the main PictoPy database and keeps the database in sync with what is
on disk.

## Layout

Mirrors `backend/app/`: `routes/`, `schemas/`, `database/`, `utils/`, `config/`, `logging/`,
plus `core/` for the file-watching machinery. The same layering rules apply — routes stay
thin, database functions are prefixed `db_`.

## Shared database

This service reads the same SQLite database as `backend/`. A schema change in
`backend/app/database/` can break it. When you change a table that this service reads,
check `sync-microservice/app/database/` for queries that need updating.

## Python rules

Identical to `backend/`: **black at 88 columns, never `ruff format`**. The same
`.pre-commit-config.yaml` at the repository root covers this directory.

```bash
pre-commit run --config ../.pre-commit-config.yaml --all-files
```
