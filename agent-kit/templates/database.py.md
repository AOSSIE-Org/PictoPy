# Template: `backend/app/database/<resource>.py`

Copy and adapt. Modelled on `backend/app/database/videos.py`.

```python
# Standard library imports
import sqlite3
from typing import Any, List, Mapping, Optional, TypedDict, Union

# App-specific imports
from app.config.settings import (
    DATABASE_PATH,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Type definitions
<Resource>Id = str


class <Resource>Record(TypedDict, total=False):
    """Represents the full <resource> table structure"""

    id: <Resource>Id
    name: str
    metadata: Union[Mapping[str, Any], str]
    created_at: Optional[str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    # Ensure ON DELETE CASCADE and other FKs are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_<resource>_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS <resource> (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def db_get_all_<resource>() -> List[<Resource>Record]:
    conn = _connect()
    try:
        cursor = conn.execute("SELECT id, name, metadata, created_at FROM <resource>")
        return [
            <Resource>Record(
                id=row[0],
                name=row[1],
                metadata=row[2],
                created_at=row[3],
            )
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()
```

## Notes

- **Every public** function here is prefixed `db_`. The prefix is what makes the data layer
  greppable across four hundred files. Module-private helpers are the exception and keep
  their leading underscore — `_connect()` is named that deliberately; do not rename it.
- Always go through `_connect()`. SQLite disables foreign-key enforcement per connection by
  default, so a direct `sqlite3.connect` silently loses `ON DELETE CASCADE`.
- `try`/`finally` around every connection — the codebase does not use context managers here
  consistently, so match the surrounding style.
- `TypedDict` with `total=False` documents the table shape without forcing every field at
  every call site.
- After adding `db_create_<resource>_table()`, call it in **both** `backend/main.py` and
  `backend/tests/conftest.py`, in the same order relative to the other tables.
