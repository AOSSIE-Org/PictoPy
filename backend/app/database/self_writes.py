"""
A short-lived record of files PictoPy modified itself.

The sync microservice watches every registered folder and treats any file change
as a user edit, so a write of our own comes straight back as a full folder
resync. Recording what we wrote lets the watcher tell the two apart.

The path format here is a contract with `sync-microservice/app/database/
self_writes.py`, which reads this table: both sides key on
`os.path.normcase(os.path.abspath(path))`.
"""

import os
import sqlite3
import time
from typing import List, Set, Tuple

from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# An entry the watcher never claims is one it missed -- it was stopped, or the
# change was coalesced away. Expiring them keeps the table bounded and limits
# how long a stale row can mask a real edit to the same path.
SELF_WRITE_TTL_SECONDS = 3600

# (path, file_size, file_mtime) as observed on disk right now.
ObservedFile = Tuple[str, int, int]


def self_write_key(path: str) -> str:
    """Normalise a path to the form both services store and look up by."""
    return os.path.normcase(os.path.abspath(path))


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def db_create_self_writes_table() -> None:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS self_writes (
                path TEXT PRIMARY KEY,
                file_size INTEGER NOT NULL,
                file_mtime INTEGER NOT NULL,
                -- Epoch seconds rather than CURRENT_TIMESTAMP: this column only
                -- exists to be subtracted from, and text timestamps make that
                -- arithmetic a timezone question.
                written_at INTEGER NOT NULL
            )
        """
        )
        conn.commit()
    finally:
        conn.close()


def db_record_self_write(path: str, file_size: int, file_mtime: int) -> bool:
    """
    Note that PictoPy is about to leave a file in this exact state.

    Callers record before the bytes land, because the watcher can fire the
    instant they do.
    """
    conn = _connect()
    cursor = conn.cursor()
    now = int(time.time())

    try:
        cursor.execute(
            """
            INSERT INTO self_writes (path, file_size, file_mtime, written_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                file_size=excluded.file_size,
                file_mtime=excluded.file_mtime,
                written_at=excluded.written_at
            """,
            (self_write_key(path), file_size, file_mtime, now),
        )
        # Pruning here avoids needing a scheduler for a table this small.
        cursor.execute(
            "DELETE FROM self_writes WHERE written_at < ?",
            (now - SELF_WRITE_TTL_SECONDS,),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error recording self write for {path}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_take_matching_self_writes(observed: List[ObservedFile]) -> Set[str]:
    """
    Return the observed paths that match a recorded write, and forget them.

    Claiming an entry as it matches means a second event for the same write is
    treated as a real change. That is the safe direction to be wrong in: it
    costs one redundant rescan, where holding the entry could swallow a genuine
    edit that happened to land in the same second at the same size.
    """
    if not observed:
        return set()

    conn = _connect()
    cursor = conn.cursor()
    matched: Set[str] = set()

    try:
        by_key = {self_write_key(path): path for path, _, _ in observed}
        placeholders = ",".join("?" for _ in observed)
        cursor.execute(
            f"""
            SELECT path, file_size, file_mtime
            FROM self_writes
            WHERE path IN ({placeholders})
            """,
            list(by_key),
        )
        recorded = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        claimed = []
        for path, size, mtime in observed:
            key = self_write_key(path)
            if recorded.get(key) == (size, mtime):
                matched.add(path)
                claimed.append(key)

        if claimed:
            cursor.executemany(
                "DELETE FROM self_writes WHERE path = ?",
                [(key,) for key in claimed],
            )
            conn.commit()

        return matched
    except sqlite3.Error as e:
        # Failing open means a redundant rescan, never a missed change.
        logger.error(f"Error matching self writes: {e}")
        return set()
    finally:
        conn.close()
