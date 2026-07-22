# AGENTS.md — backend

Rules for the Python FastAPI backend. The root `AGENTS.md` still applies.

## Layering

A feature is spread across four layers. Follow the chain; do not collapse it.

| Layer | Path | Convention |
| --- | --- | --- |
| Route | `app/routes/<resource>.py` | `router = APIRouter()`, Pydantic models in-file |
| Schema | `app/schemas/<resource>.py` | shared models, notably `ErrorResponse` |
| Database | `app/database/<resource>.py` | every function prefixed `db_` |
| Utils | `app/utils/<domain>.py` | pure helpers, no FastAPI imports |

`app/routes/videos.py` and `app/database/videos.py` are the cleanest reference pair. Read
them before writing a new resource.

## Routes

- `logger = get_logger(__name__)` from `app.logging.setup_logging`, right after the imports.
- Declare response models as Pydantic classes in the route file itself.
- Every route declares `responses={500: {"model": ErrorResponse}}` and imports
  `ErrorResponse` from `app/schemas/<resource>.py`.
- Return `{success, message, data}` shaped responses.
- **Build list responses row by row.** One record with unusable metadata must not 500 the
  whole listing and hide every other row — see `get_all_videos` for the pattern.

## Database

- SQLite. Every function that touches it is prefixed `db_`.
- Record shapes are `TypedDict` classes (`VideoRecord`, etc.), not bare dicts.
- Connect through the module-private `_connect()`, which sets
  `PRAGMA foreign_keys = ON`. Do not call `sqlite3.connect` directly.

## Wiring a new resource

Miss one of these and it silently half-works:

1. Register the router in `main.py`.
2. Call the new `db_create_*_table()` in `main.py`.
3. Call it again in `tests/conftest.py`, **in the same order** — the ordering encodes
   foreign-key dependencies.
4. Mirror the endpoint paths in `frontend/src/api/apiEndpoints.ts`.

## Tests

- `tests/test_<resource>.py`. Config in `pytest.ini`: `pythonpath = .`, `testpaths = tests`.
- The session fixture in `conftest.py` creates every table and sets `TEST_MODE=true`.
- Run with `cd backend && pytest`.

## Environment

No virtualenv is committed. Create your own and
`pip install -r backend/requirements.txt` into it. ONNX models download at runtime.

## Formatting

**black**, 88 columns. Never `ruff format` — see the root `AGENTS.md` for why.
Verify with `pre-commit run --config ../.pre-commit-config.yaml --all-files`.
