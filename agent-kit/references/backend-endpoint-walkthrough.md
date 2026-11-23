# Backend endpoint walkthrough

The `videos` resource traced through every layer. It is the cleanest complete example in
the backend — read it before adding a new resource.

## The files

```text
backend/app/routes/videos.py       # HTTP surface
backend/app/schemas/videos.py      # shared Pydantic models (ErrorResponse)
backend/app/database/videos.py     # SQLite access, all db_-prefixed
backend/main.py                    # router registration + table creation
backend/tests/conftest.py          # table creation for tests
backend/tests/test_videos.py       # tests
frontend/src/api/apiEndpoints.ts   # URL mirror on the frontend
```

## Route layer

`backend/app/routes/videos.py` opens with the shape every route file follows:

- imports, then `logger = get_logger(__name__)`, then `router = APIRouter()`
- Pydantic response models declared in the file — `VideoMetadataModel`, `VideoData`,
  `GetAllVideosResponse`
- `ErrorResponse` imported from `app/schemas/videos.py`, not redefined

Each route declares its error contract:

```python
@router.get(
    "/",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_videos():
    """Get all videos from the database."""
```

### The row-by-row rule

`get_all_videos` builds its list one record at a time inside a `try`, so a single row with
unusable metadata cannot 500 the request and hide every other video. This is a deliberate
convention, not incidental — copy it for any endpoint returning a collection.

## Database layer

`backend/app/database/videos.py` shows the three conventions:

1. **Type aliases and `TypedDict` records** — `VideoId`, `VideoPath`, `VideoRecord`. The
   record class documents the table's columns in one place.
2. **`_connect()`** — module-private, and it sets `PRAGMA foreign_keys = ON` on every
   connection. SQLite does not enforce foreign keys unless you ask, per connection. Never
   call `sqlite3.connect` directly.
3. **`db_` prefix on everything** — `db_get_all_videos`, `db_create_videos_table`,
   `db_toggle_video_favourite_status`. Grep-ability is the point.

## The wiring

`main.py` does two separate things for each resource, and both are easy to miss:

```python
from app.database.videos import db_create_videos_table
from app.routes.videos import router as videos_router
```

The table creation calls run in a fixed order in `main.py`, and **the same order is
repeated in `tests/conftest.py`**. The ordering encodes foreign-key dependencies — clusters
before faces, folders before images. Adding a table to one file and not the other produces
tests that fail with a missing-table error while the app runs fine, or vice versa.

## The frontend mirror

`frontend/src/api/apiEndpoints.ts` holds the URLs:

```ts
export const videosEndpoints = {
  getAllVideos: '/videos/',
  setFavourite: '/videos/toggle-favourite',
};
```

Nothing in the frontend hardcodes a backend path outside this file. When you add a route,
add it here in the same commit — otherwise the next frontend contributor invents a second
source of truth.

## Tests

`backend/tests/test_videos.py` runs against a real SQLite database: the session fixture in
`conftest.py` creates every table and sets `TEST_MODE=true` before any test runs, then
tears down afterwards. There is no mocking layer to satisfy.
