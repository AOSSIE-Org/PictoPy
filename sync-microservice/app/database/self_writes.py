"""
Reads the self-write ledger the primary backend maintains.

The table is created and populated by `backend/app/database/self_writes.py`;
this service only claims entries. The path format is a contract with that
module: both sides key on `os.path.normcase(os.path.abspath(path))`.
"""

import os
import sqlite3
from typing import List, Set, Tuple

from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_sync_logger

logger = get_sync_logger(__name__)

# (path, file_size, file_mtime) as observed on disk right now.
ObservedFile = Tuple[str, int, int]


def _self_write_key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def db_take_matching_self_writes(observed: List[ObservedFile]) -> Set[str]:
    """
    Return the observed paths PictoPy wrote itself, and claim them.

    Claiming as we match means a second event for one write reads as a real
    change. That is the safe direction: it costs a redundant rescan, where
    keeping the entry could swallow a genuine edit to the same path.
    """
    if not observed:
        return set()

    conn = None
    matched: Set[str] = set()

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        keys = {_self_write_key(path) for path, _, _ in observed}
        placeholders = ",".join("?" for _ in keys)
        cursor.execute(
            f"""
            SELECT path, file_size, file_mtime
            FROM self_writes
            WHERE path IN ({placeholders})
            """,
            list(keys),
        )
        recorded = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        claimed = []
        for path, size, mtime in observed:
            key = _self_write_key(path)
            if recorded.get(key) == (size, mtime):
                matched.add(path)
                claimed.append((key,))

        if claimed:
            cursor.executemany("DELETE FROM self_writes WHERE path = ?", claimed)
            conn.commit()

        return matched
    except sqlite3.Error as e:
        # Failing open costs a redundant rescan; failing closed would drop a
        # real change, so an unreadable ledger must never suppress anything.
        logger.error(f"Error matching self writes: {e}")
        return set()
    finally:
        if conn is not None:
            conn.close()
