---
name: add-backend-endpoint
description: Scaffold a FastAPI endpoint in the PictoPy backend across all four layers. Use when adding a backend route, API endpoint, or new backend resource.
argument-hint: [resource-name]
---

# Add a backend endpoint

A backend feature spans four layers plus wiring. Skipping a step produces something that
half-works: the route returns 200 but the table was never created, or the frontend cannot
reach it.

`$1` is the resource name (singular or plural as the domain reads naturally — the existing
code uses `videos`, `albums`, `folders`).

Work through this in order. Read `agent-kit/references/backend-endpoint-walkthrough.md`
for the `videos` resource traced end to end — it is the cleanest example in the codebase.

## 1. Understand the shape first

Before writing anything, read the closest existing analogue:

```text
backend/app/routes/videos.py
backend/app/database/videos.py
backend/app/schemas/videos.py
```

If the resource already has some layers, extend them rather than creating parallel ones.

## 2. Database layer — `backend/app/database/<resource>.py`

Template: `agent-kit/templates/database.py.md`.

- Every function that touches SQLite is prefixed `db_`.
- Record shapes are `TypedDict` classes, not bare dicts.
- Connect through the module-private `_connect()`, which sets
  `PRAGMA foreign_keys = ON`. Never call `sqlite3.connect` directly.
- Include a `db_create_<resource>_table()` if this introduces a table.

## 3. Schema layer — `backend/app/schemas/<resource>.py`

Shared Pydantic models, and `ErrorResponse` if the resource does not already have one.
Models used by exactly one route stay in the route file instead.

## 4. Route layer — `backend/app/routes/<resource>.py`

Template: `agent-kit/templates/route.py.md`.

- `router = APIRouter()` and `logger = get_logger(__name__)` after the imports.
- Response models as Pydantic classes in the route file.
- `responses={500: {"model": ErrorResponse}}` on every route.
- Return `{success, message, data}`.
- **Build list responses row by row.** One record with unusable metadata must not 500 the
  whole listing and hide every other row. `get_all_videos` shows the pattern.

## 5. Wire it up — four places, all required

1. `backend/main.py` — import the router and register it.
2. `backend/main.py` — call `db_create_<resource>_table()` alongside the others.
3. `backend/tests/conftest.py` — call it again, **in the same order as `main.py`**. The
   order encodes foreign-key dependencies; getting it wrong makes tests fail confusingly.
4. `frontend/src/api/apiEndpoints.ts` — mirror the paths in a `<resource>Endpoints` object,
   so the frontend has a single source of truth for URLs.

## 6. Tests — `backend/tests/test_<resource>.py`

Follow `backend/tests/test_videos.py`. Cover the success path, the empty case, and at least
one failure path. The session fixture in `conftest.py` creates every table and sets
`TEST_MODE=true`, so tests get a real database.

## 7. Verify

```bash
cd backend && pytest
pre-commit run --config ../.pre-commit-config.yaml --all-files
```

black reformats to 88 columns. **Never run `ruff format`** — Ruff is configured at 300
columns here and would reflow the whole codebase.

If this change touched a table that `sync-microservice/` also reads, check
`sync-microservice/app/database/` for queries that need updating.

## Checklist

- [ ] `database/<resource>.py` with `db_`-prefixed functions and `TypedDict` records
- [ ] `schemas/<resource>.py` if shared models are needed
- [ ] `routes/<resource>.py` with logger, `ErrorResponse`, row-by-row list building
- [ ] Router registered in `main.py`
- [ ] Table created in `main.py` **and** `tests/conftest.py`, same order
- [ ] Endpoints mirrored in `frontend/src/api/apiEndpoints.ts`
- [ ] `tests/test_<resource>.py` covering success, empty, and failure
- [ ] `pytest` and `pre-commit` both pass
