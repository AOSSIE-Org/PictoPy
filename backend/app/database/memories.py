# This DB module stores curated memories: persisted, scored collections of
# images surfaced proactively rather than browsed.
import json
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, TypedDict

from app.database.images import _connect
from app.database.semantic_labels import SEMANTIC_CLASS_ID_OFFSET
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

MemoryId = str
ImageId = str

EVENT_TYPES = ("anniversary", "import_event", "semantic_event")
MEMORY_STATUSES = ("pending", "complete", "failed", "empty")
RUN_STATUSES = ("running", "complete", "failed")

# (image_id, sort_order, score)
MemoryImageEntry = Tuple[ImageId, int, Optional[float]]

# Columns settable by db_upsert_memory. memory_id, viewed_at, notified_at and
# dismissed are deliberately excluded: re-curation replaces contents without
# resetting what the user has already seen.
_UPSERT_COLUMNS = (
    "event_type",
    "status",
    "title",
    "subtitle",
    "place_label",
    "center_lat",
    "center_lon",
    "surface_date",
    "period_start",
    "period_end",
    "cover_image_id",
    "image_count",
    "score",
    "signals",
    "params_signature",
    "error",
)


class MemoryRecord(TypedDict, total=False):
    """Represents a row of the memories table."""

    memory_id: MemoryId
    dedupe_key: str
    event_type: str
    status: str
    title: str
    subtitle: Optional[str]
    place_label: Optional[str]
    center_lat: Optional[float]
    center_lon: Optional[float]
    surface_date: str
    period_start: Optional[str]
    period_end: Optional[str]
    cover_image_id: Optional[ImageId]
    image_count: int
    score: float
    signals: Optional[Dict[str, Any]]
    params_signature: Optional[str]
    error: Optional[str]


def db_create_memories_table() -> None:
    """Create the memories, memory_images and memory_runs tables."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                dedupe_key TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL
                    CHECK (event_type IN
                        ('anniversary', 'import_event', 'semantic_event')),
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'complete', 'failed', 'empty')),
                title TEXT NOT NULL,
                subtitle TEXT,
                place_label TEXT,
                center_lat REAL,
                center_lon REAL,
                surface_date DATE NOT NULL,
                period_start DATETIME,
                period_end DATETIME,
                cover_image_id TEXT,
                image_count INTEGER NOT NULL DEFAULT 0,
                score REAL NOT NULL DEFAULT 0,
                signals TEXT,
                params_signature TEXT,
                error TEXT,
                notified_at DATETIME,
                viewed_at DATETIME,
                dismissed BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cover_image_id) REFERENCES images(id) ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_images (
                memory_id TEXT NOT NULL,
                image_id TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                score REAL,
                PRIMARY KEY (memory_id, image_id),
                FOREIGN KEY (memory_id) REFERENCES memories(memory_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )

        # One row per curation run. "Zero memories today" is a legitimate
        # outcome, so "did I already run?" is unanswerable from memories alone.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_runs (
                run_date DATE PRIMARY KEY,
                status TEXT NOT NULL
                    CHECK (status IN ('running', 'complete', 'failed')),
                params_signature TEXT,
                generated_count INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME
            )
            """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_memories_surface_date "
            "ON memories(surface_date DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_memories_status_surface "
            "ON memories(status, surface_date DESC)"
        )
        # Backs the launch-time "is there anything to show?" lookup.
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_memories_surfaceable "
            "ON memories(surface_date DESC, score DESC) "
            "WHERE viewed_at IS NULL AND dismissed = 0 AND status = 'complete'"
        )
        # Without this SQLite scans memory_images on every image delete.
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_memory_images_image_id "
            "ON memory_images(image_id)"
        )

        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def _row_to_memory(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a memories row to a dict, decoding the signals JSON blob."""
    memory = dict(row)
    raw_signals = memory.get("signals")
    if raw_signals:
        try:
            memory["signals"] = json.loads(raw_signals)
        except (TypeError, json.JSONDecodeError):
            memory["signals"] = None
    else:
        memory["signals"] = None
    memory["dismissed"] = bool(memory.get("dismissed"))
    return memory


def db_upsert_memory(
    memory: MemoryRecord, images: Sequence[MemoryImageEntry]
) -> Optional[MemoryId]:
    """
    Insert or replace a memory and its image set in one transaction.

    Conflicts resolve on dedupe_key, keeping the existing memory_id and the
    user's viewed_at/notified_at/dismissed state. Returns the surviving
    memory_id, or None on failure.
    """
    dedupe_key = memory.get("dedupe_key")
    memory_id = memory.get("memory_id")
    if not dedupe_key or not memory_id:
        raise ValueError("memory requires both memory_id and dedupe_key")

    signals = memory.get("signals")
    values: Dict[str, Any] = {
        "memory_id": memory_id,
        "dedupe_key": dedupe_key,
        "event_type": memory["event_type"],
        "status": memory.get("status", "pending"),
        "title": memory["title"],
        "subtitle": memory.get("subtitle"),
        "place_label": memory.get("place_label"),
        "center_lat": memory.get("center_lat"),
        "center_lon": memory.get("center_lon"),
        "surface_date": memory["surface_date"],
        "period_start": memory.get("period_start"),
        "period_end": memory.get("period_end"),
        "cover_image_id": memory.get("cover_image_id"),
        "image_count": memory.get("image_count", len(images)),
        "score": memory.get("score", 0.0),
        "signals": json.dumps(signals) if signals is not None else None,
        "params_signature": memory.get("params_signature"),
        "error": memory.get("error"),
    }

    columns = ["memory_id", "dedupe_key", *_UPSERT_COLUMNS]
    placeholders = ", ".join(f":{name}" for name in columns)
    updates = ", ".join(f"{name} = excluded.{name}" for name in _UPSERT_COLUMNS)

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO memories ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(dedupe_key) DO UPDATE SET
                {updates},
                updated_at = CURRENT_TIMESTAMP
            """,
            values,
        )

        # Re-read: on conflict the surviving id is the pre-existing one.
        cursor.execute(
            "SELECT memory_id FROM memories WHERE dedupe_key = ?", (dedupe_key,)
        )
        row = cursor.fetchone()
        if row is None:
            conn.rollback()
            return None
        resolved_id = row[0]

        cursor.execute("DELETE FROM memory_images WHERE memory_id = ?", (resolved_id,))
        if images:
            cursor.executemany(
                "INSERT INTO memory_images (memory_id, image_id, sort_order, score) "
                "VALUES (?, ?, ?, ?)",
                [
                    (resolved_id, image_id, sort_order, score)
                    for image_id, sort_order, score in images
                ],
            )

        conn.commit()
        return resolved_id
    except sqlite3.Error as e:
        if conn is not None:
            conn.rollback()
        logger.error(f"Error upserting memory {dedupe_key}: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()


def db_mark_memory(
    memory_id: MemoryId,
    *,
    viewed: Optional[bool] = None,
    dismissed: Optional[bool] = None,
    notified: Optional[bool] = None,
) -> bool:
    """Set the viewed/dismissed/notified state of a memory independently."""
    assignments: List[str] = []
    params: List[Any] = []

    if viewed is not None:
        assignments.append(
            "viewed_at = CURRENT_TIMESTAMP" if viewed else "viewed_at = NULL"
        )
    if notified is not None:
        assignments.append(
            "notified_at = CURRENT_TIMESTAMP" if notified else "notified_at = NULL"
        )
    if dismissed is not None:
        assignments.append("dismissed = ?")
        params.append(1 if dismissed else 0)

    if not assignments:
        return False

    assignments.append("updated_at = CURRENT_TIMESTAMP")
    params.append(memory_id)

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE memories SET {', '.join(assignments)} WHERE memory_id = ?",
            params,
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if conn is not None:
            conn.close()


def db_delete_memory(memory_id: MemoryId) -> bool:
    """Delete a memory; its memory_images rows cascade."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if conn is not None:
            conn.close()


def db_prune_empty_memories(min_images: int) -> int:
    """
    Mark memories whose live image count fell below min_images as 'empty'.

    Images deleted from the library cascade out of memory_images, so a memory
    can silently shrink below the point where it is worth surfacing.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE memories SET status = 'empty', updated_at = CURRENT_TIMESTAMP
            WHERE status = 'complete'
              AND (SELECT COUNT(*) FROM memory_images mi
                    WHERE mi.memory_id = memories.memory_id) < ?
            """,
            (min_images,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        if conn is not None:
            conn.close()


def db_delete_stale_memories() -> int:
    """
    Delete memories holding a photo whose capture date has since moved.

    period_start/period_end are the min and max of exactly these images, so a
    member sitting outside that window means the dates underneath the memory
    changed after it was built — a re-extraction correcting an EXIF read, or a
    guessed date being withdrawn. The memory now claims an occasion that never
    happened, and no rebuild reaches it: its dedupe_key encodes the old dates,
    so curation never generates that key again.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM memories
            WHERE period_start IS NOT NULL
              AND period_end IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM memory_images mi
                  JOIN images i ON i.id = mi.image_id
                  WHERE mi.memory_id = memories.memory_id
                    AND (i.captured_at IS NULL
                         OR datetime(i.captured_at)
                            < datetime(memories.period_start)
                         OR datetime(i.captured_at)
                            > datetime(memories.period_end))
              )
            """
        )
        conn.commit()
        return cursor.rowcount
    finally:
        if conn is not None:
            conn.close()


def db_get_memory(memory_id: MemoryId) -> Optional[Dict[str, Any]]:
    """Get a single memory row with its live image count and cover thumbnail."""
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.*,
                   (SELECT COUNT(*) FROM memory_images mi
                     WHERE mi.memory_id = m.memory_id) AS live_image_count,
                   ci.thumbnailPath AS cover_thumbnail_path
            FROM memories m
            LEFT JOIN images ci ON ci.id = m.cover_image_id
            WHERE m.memory_id = ?
            """,
            (memory_id,),
        )
        row = cursor.fetchone()
        return _row_to_memory(row) if row else None
    finally:
        if conn is not None:
            conn.close()


def db_get_memory_images(memory_id: MemoryId) -> List[Dict[str, Any]]:
    """Get a memory's curated images in presentation order."""
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.id, i.path, i.thumbnailPath, i.captured_at,
                   i.latitude, i.longitude, i.isFavourite,
                   mi.sort_order, mi.score
            FROM memory_images mi
            JOIN images i ON i.id = mi.image_id
            WHERE mi.memory_id = ?
            ORDER BY mi.sort_order ASC
            """,
            (memory_id,),
        )
        images = []
        for row in cursor.fetchall():
            image = dict(row)
            image["isFavourite"] = bool(image.get("isFavourite"))
            images.append(image)
        return images
    finally:
        if conn is not None:
            conn.close()


def db_list_memories(
    limit: int = 30,
    offset: int = 0,
    event_type: Optional[str] = None,
    include_viewed: bool = True,
    include_dismissed: bool = False,
) -> Tuple[List[Dict[str, Any]], int]:
    """List memory cards newest first. Returns (rows, total matching count)."""
    filters = ["m.status = 'complete'"]
    params: List[Any] = []

    if event_type:
        filters.append("m.event_type = ?")
        params.append(event_type)
    if not include_viewed:
        filters.append("m.viewed_at IS NULL")
    if not include_dismissed:
        filters.append("m.dismissed = 0")

    where = " AND ".join(filters)

    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM memories m WHERE {where}", params)
        total_count = cursor.fetchone()[0]

        cursor.execute(
            f"""
            SELECT m.*,
                   (SELECT COUNT(*) FROM memory_images mi
                     WHERE mi.memory_id = m.memory_id) AS live_image_count,
                   ci.thumbnailPath AS cover_thumbnail_path
            FROM memories m
            LEFT JOIN images ci ON ci.id = m.cover_image_id
            WHERE {where}
            ORDER BY m.surface_date DESC, m.score DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        )
        memories = [_row_to_memory(row) for row in cursor.fetchall()]
        return memories, total_count
    finally:
        if conn is not None:
            conn.close()


def db_get_surfaceable_memory(reference_date: str) -> Optional[Dict[str, Any]]:
    """
    Get the single best memory to surface now.

    Unviewed, undismissed, complete, and not dated in the future. Highest
    surface_date wins, then highest score.
    """
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.*,
                   (SELECT COUNT(*) FROM memory_images mi
                     WHERE mi.memory_id = m.memory_id) AS live_image_count,
                   ci.thumbnailPath AS cover_thumbnail_path
            FROM memories m
            LEFT JOIN images ci ON ci.id = m.cover_image_id
            WHERE m.status = 'complete'
              AND m.viewed_at IS NULL
              AND m.dismissed = 0
              AND m.surface_date <= ?
            ORDER BY m.surface_date DESC, m.score DESC
            LIMIT 1
            """,
            (reference_date,),
        )
        row = cursor.fetchone()
        return _row_to_memory(row) if row else None
    finally:
        if conn is not None:
            conn.close()


def db_get_existing_dedupe_keys(params_signature: Optional[str] = None) -> Set[str]:
    """
    Get dedupe keys already generated.

    Passing params_signature returns only keys generated under that signature,
    so memories built by an older scorer are treated as regenerable.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        if params_signature is None:
            cursor.execute("SELECT dedupe_key FROM memories")
        else:
            cursor.execute(
                "SELECT dedupe_key FROM memories WHERE params_signature = ?",
                (params_signature,),
            )
        return {row[0] for row in cursor.fetchall()}
    finally:
        if conn is not None:
            conn.close()


def db_get_recently_used_image_ids(days: int, reference_date: str) -> Set[ImageId]:
    """Get image ids used by memories surfaced within the last `days` days."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT mi.image_id
            FROM memory_images mi
            JOIN memories m ON m.memory_id = mi.memory_id
            WHERE m.surface_date >= date(?, ?)
            """,
            (reference_date, f"-{days} days"),
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        if conn is not None:
            conn.close()


def db_count_unviewed_memories(reference_date: str) -> int:
    """Count surfaceable memories the user has not opened yet."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM memories
            WHERE status = 'complete' AND viewed_at IS NULL
              AND dismissed = 0 AND surface_date <= ?
            """,
            (reference_date,),
        )
        return cursor.fetchone()[0]
    finally:
        if conn is not None:
            conn.close()


def db_is_indexing_busy() -> bool:
    """
    Report whether any folder is mid-index or mid-tagging.

    Curating during either would score a half-written image set, so this gates
    the scheduler. Exposed over HTTP so the Tauri task never opens SQLite.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT EXISTS(
                       SELECT 1 FROM folders WHERE indexing_status = 'in_progress'
                   )
                OR EXISTS(
                       SELECT 1 FROM folders
                        WHERE AI_Tagging = 1 AND IFNULL(taggingCompleted, 0) = 0
                   )
            """
        )
        return bool(cursor.fetchone()[0])
    finally:
        if conn is not None:
            conn.close()


def db_start_memory_run(run_date: str, params_signature: Optional[str] = None) -> bool:
    """Mark a curation run as running, resetting any prior run for that date."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memory_runs
                (run_date, status, params_signature, generated_count, error,
                 started_at, finished_at)
            VALUES (?, 'running', ?, 0, NULL, CURRENT_TIMESTAMP, NULL)
            ON CONFLICT(run_date) DO UPDATE SET
                status = 'running',
                params_signature = excluded.params_signature,
                generated_count = 0,
                error = NULL,
                started_at = CURRENT_TIMESTAMP,
                finished_at = NULL
            """,
            (run_date, params_signature),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if conn is not None:
            conn.close()


def db_finish_memory_run(
    run_date: str,
    status: str,
    generated_count: int = 0,
    error: Optional[str] = None,
) -> bool:
    """Mark a curation run as complete or failed."""
    if status not in ("complete", "failed"):
        raise ValueError(f"invalid terminal run status: {status}")

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE memory_runs
               SET status = ?, generated_count = ?, error = ?,
                   finished_at = CURRENT_TIMESTAMP
             WHERE run_date = ?
            """,
            (status, generated_count, error, run_date),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if conn is not None:
            conn.close()


def db_get_memory_run(run_date: str) -> Optional[Dict[str, Any]]:
    """Get the run record for a date."""
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memory_runs WHERE run_date = ?", (run_date,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if conn is not None:
            conn.close()


def db_reap_stale_memory_runs(stale_minutes: int = 30) -> int:
    """
    Fail runs left 'running' past the staleness window.

    Closing the app mid-generation would otherwise leave a run that blocks
    every future one. Reaping it silently lets the next call regenerate.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE memory_runs
               SET status = 'failed',
                   error = 'Interrupted: run exceeded the staleness window',
                   finished_at = CURRENT_TIMESTAMP
             WHERE status = 'running'
               AND started_at < datetime('now', ?)
            """,
            (f"-{stale_minutes} minutes",),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        if conn is not None:
            conn.close()


def db_get_recent_dated_images(limit: int) -> List[Dict[str, Any]]:
    """
    Get the most recently captured images, oldest first within the window.

    The import-event candidate pool. Deliberately independent of what is
    already curated: a pool defined as "not yet in a memory" flips to its own
    complement every time a memory is written, so regenerating would swap the
    contents of a memory rather than reproduce them.
    """
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, path, thumbnailPath, captured_at, latitude, longitude,
                   isFavourite
            FROM images
            WHERE captured_at IS NOT NULL
            ORDER BY datetime(captured_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = []
        for row in cursor.fetchall():
            image = dict(row)
            image["isFavourite"] = bool(image.get("isFavourite"))
            rows.append(image)
        rows.reverse()
        return rows
    finally:
        if conn is not None:
            conn.close()


def db_get_memory_image_ids_by_dedupe_key(dedupe_key: str) -> Set[ImageId]:
    """
    Image ids already held by the memory with this dedupe key.

    Rebuilding a memory must be allowed to reuse its own photos; only other
    memories' photos are off limits.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT mi.image_id FROM memory_images mi
            JOIN memories m ON m.memory_id = mi.memory_id
            WHERE m.dedupe_key = ?
            """,
            (dedupe_key,),
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        if conn is not None:
            conn.close()


def db_get_anniversary_candidates(
    month_days: Sequence[str], max_year: int
) -> List[Dict[str, Any]]:
    """
    Get images captured on the given MM-DD dates in years up to max_year.

    One query across the whole window, rather than a per-year loop. Callers
    pass a +/-1 day window to absorb timezone and EXIF drift.
    """
    if not month_days:
        return []

    placeholders = ", ".join("?" * len(month_days))
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, path, thumbnailPath, captured_at, latitude, longitude,
                   isFavourite,
                   CAST(strftime('%Y', captured_at) AS INTEGER) AS capture_year
            FROM images
            WHERE captured_at IS NOT NULL
              AND strftime('%m-%d', captured_at) IN ({placeholders})
              AND CAST(strftime('%Y', captured_at) AS INTEGER) <= ?
            ORDER BY captured_at ASC
            """,
            [*month_days, max_year],
        )
        rows = []
        for row in cursor.fetchall():
            image = dict(row)
            image["isFavourite"] = bool(image.get("isFavourite"))
            rows.append(image)
        return rows
    finally:
        if conn is not None:
            conn.close()


def db_get_images_by_ids_for_memories(
    image_ids: Sequence[ImageId],
) -> List[Dict[str, Any]]:
    """Get the image fields a memory needs, for an explicit id list."""
    if not image_ids:
        return []

    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows: List[Dict[str, Any]] = []
        for start in range(0, len(image_ids), 500):
            chunk = list(image_ids[start : start + 500])
            placeholders = ", ".join("?" * len(chunk))
            cursor.execute(
                f"""
                SELECT id, path, thumbnailPath, captured_at, latitude, longitude,
                       isFavourite
                FROM images WHERE id IN ({placeholders})
                """,
                chunk,
            )
            for row in cursor.fetchall():
                image = dict(row)
                image["isFavourite"] = bool(image.get("isFavourite"))
                rows.append(image)
        return rows
    finally:
        if conn is not None:
            conn.close()


def db_get_memory_ids_for_cluster(cluster_id: str) -> List[MemoryId]:
    """Ids of complete memories holding at least one face from a cluster."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT mi.memory_id
            FROM memory_images mi
            JOIN faces f ON f.image_id = mi.image_id
            JOIN memories m ON m.memory_id = mi.memory_id
            WHERE f.cluster_id = ? AND m.status = 'complete'
            """,
            (cluster_id,),
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        if conn is not None:
            conn.close()


def db_update_memory_scores(
    memory_id: MemoryId,
    image_scores: Sequence[Tuple[ImageId, float]],
    cover_image_id: Optional[ImageId],
    score: float,
) -> bool:
    """
    Rewrite the scores of a memory's existing images.

    Membership and order are untouched: this exists so a change in scoring
    inputs can be reflected without reshuffling a memory the user may already
    have seen.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.executemany(
            "UPDATE memory_images SET score = ? WHERE memory_id = ? AND image_id = ?",
            [
                (image_score, memory_id, image_id)
                for image_id, image_score in image_scores
            ],
        )
        cursor.execute(
            """
            UPDATE memories
               SET cover_image_id = ?, score = ?, updated_at = CURRENT_TIMESTAMP
             WHERE memory_id = ?
            """,
            (cover_image_id, score, memory_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        if conn is not None:
            conn.rollback()
        logger.error(f"Error updating scores for memory {memory_id}: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()


def db_get_scoring_signals(image_ids: Sequence[ImageId]) -> List[Dict[str, Any]]:
    """
    Collect every raw scoring signal for a candidate set in one pass.

    Correlated subqueries rather than joins: each is a point lookup on an
    indexed column, and a multi-way join over faces/albums/classes would
    fan out rows and need re-aggregating.
    """
    if not image_ids:
        return []

    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows: List[Dict[str, Any]] = []
        for start in range(0, len(image_ids), 500):
            chunk = list(image_ids[start : start + 500])
            placeholders = ", ".join("?" * len(chunk))
            cursor.execute(
                f"""
                SELECT
                  i.id,
                  i.isFavourite,
                  i.latitude,
                  i.longitude,
                  i.captured_at,
                  (SELECT COUNT(*) FROM faces f WHERE f.image_id = i.id)
                      AS face_count,
                  (SELECT COUNT(DISTINCT f.cluster_id)
                     FROM faces f
                     JOIN face_clusters fc ON fc.cluster_id = f.cluster_id
                    WHERE f.image_id = i.id
                      AND fc.cluster_name IS NOT NULL
                      AND TRIM(fc.cluster_name) != '') AS named_people,
                  (SELECT MAX(ic.score) FROM image_classes ic
                    WHERE ic.image_id = i.id
                      AND ic.class_id >= {SEMANTIC_CLASS_ID_OFFSET})
                      AS top_semantic_score,
                  (SELECT MAX(ic.score) FROM image_classes ic
                     JOIN semantic_labels sl ON sl.class_id = ic.class_id
                    WHERE ic.image_id = i.id AND sl.category = 'event')
                      AS top_event_score,
                  (SELECT COUNT(DISTINCT ic.class_id) FROM image_classes ic
                    WHERE ic.image_id = i.id) AS class_count,
                  EXISTS(SELECT 1 FROM album_images ai WHERE ai.image_id = i.id)
                      AS in_album,
                  (SELECT e.scored_signature FROM image_embeddings e
                    WHERE e.image_id = i.id) AS scored_signature
                FROM images i
                WHERE i.id IN ({placeholders})
                """,
                chunk,
            )
            for row in cursor.fetchall():
                signals = dict(row)
                signals["isFavourite"] = bool(signals.get("isFavourite"))
                signals["in_album"] = bool(signals.get("in_album"))
                rows.append(signals)
        return rows
    finally:
        if conn is not None:
            conn.close()


def db_get_gps_histogram(
    precision: int = 1, min_images: int = 1
) -> List[Tuple[float, float, int]]:
    """
    Count geotagged images per rounded lat/lon cell, densest first.

    At precision 1 a cell is roughly 11 km, which is the right granularity for
    picking out where the user actually lives.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ROUND(latitude, ?) AS cell_lat,
                   ROUND(longitude, ?) AS cell_lon,
                   COUNT(*) AS image_count
            FROM images
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY cell_lat, cell_lon
            HAVING image_count >= ?
            ORDER BY image_count DESC
            """,
            (precision, precision, min_images),
        )
        return [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    finally:
        if conn is not None:
            conn.close()


def db_get_gps_cell_centre(
    cell_lat: float, cell_lon: float, precision: int = 1
) -> Optional[Tuple[float, float]]:
    """Mean coordinate of the images inside one rounded GPS cell."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT AVG(latitude), AVG(longitude) FROM images
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND ROUND(latitude, ?) = ? AND ROUND(longitude, ?) = ?
            """,
            (precision, cell_lat, precision, cell_lon),
        )
        row = cursor.fetchone()
        if row is None or row[0] is None:
            return None
        return (row[0], row[1])
    finally:
        if conn is not None:
            conn.close()


def db_get_event_labels() -> List[Dict[str, Any]]:
    """
    Active event labels from the semantic vocabulary.

    Read from the table rather than hardcoded, so vocabulary edits flow
    through to curation without a code change.
    """
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT class_id, name FROM semantic_labels
            WHERE category = 'event' AND active = 1
            ORDER BY class_id
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if conn is not None:
            conn.close()


def db_get_event_label_hits(
    class_ids: Sequence[int], min_score: float
) -> List[Dict[str, Any]]:
    """Images scoring above min_score for any of the given event labels."""
    if not class_ids:
        return []

    placeholders = ", ".join("?" * len(class_ids))
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT ic.image_id, ic.class_id, ic.score,
                   i.captured_at, i.latitude, i.longitude
            FROM image_classes ic
            JOIN images i ON i.id = ic.image_id
            WHERE ic.class_id IN ({placeholders})
              AND ic.score >= ?
              AND i.captured_at IS NOT NULL
            ORDER BY ic.class_id, i.captured_at
            """,
            [*class_ids, min_score],
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if conn is not None:
            conn.close()


def db_get_top_event_label(
    image_ids: Sequence[ImageId], min_score: float
) -> Optional[Tuple[int, str, float]]:
    """
    Strongest event label across a set of images, by summed score.

    Names an import-event memory ("Birthday · March 2024") when the AI
    pipeline has already recognised what the photos show.
    """
    if not image_ids:
        return None

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        best: Optional[Tuple[int, str, float]] = None
        totals: Dict[int, Tuple[str, float]] = {}
        for start in range(0, len(image_ids), 500):
            chunk = list(image_ids[start : start + 500])
            placeholders = ", ".join("?" * len(chunk))
            cursor.execute(
                f"""
                SELECT ic.class_id, sl.name, SUM(ic.score) AS total
                FROM image_classes ic
                JOIN semantic_labels sl ON sl.class_id = ic.class_id
                WHERE sl.category = 'event' AND sl.active = 1
                  AND ic.score >= ? AND ic.image_id IN ({placeholders})
                GROUP BY ic.class_id, sl.name
                """,
                [min_score, *chunk],
            )
            for class_id, name, total in cursor.fetchall():
                existing = totals.get(class_id)
                running = (existing[1] if existing else 0.0) + (total or 0.0)
                totals[class_id] = (name, running)

        for class_id, (name, total) in totals.items():
            if best is None or total > best[2]:
                best = (class_id, name, total)
        return best
    finally:
        if conn is not None:
            conn.close()


def db_get_images_in_period(
    period_start: str, period_end: str, exclude_ids: Sequence[ImageId] = ()
) -> List[Dict[str, Any]]:
    """
    Images captured inside a time span.

    Used to pull the unlabeled candids that sit between the labelled shots of
    an event; those are what make a memory read as a story.
    """
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Compared through datetime() rather than as raw strings: stored
        # timestamps use a space separator while ISO bounds use "T", and "T"
        # sorts after every digit, so a direct comparison silently matches
        # nothing.
        cursor.execute(
            """
            SELECT id, path, thumbnailPath, captured_at, latitude, longitude,
                   isFavourite
            FROM images
            WHERE captured_at IS NOT NULL
              AND datetime(captured_at) >= datetime(?)
              AND datetime(captured_at) <= datetime(?)
            ORDER BY datetime(captured_at)
            """,
            (period_start, period_end),
        )
        excluded = set(exclude_ids)
        rows = []
        for row in cursor.fetchall():
            if row["id"] in excluded:
                continue
            image = dict(row)
            image["isFavourite"] = bool(image.get("isFavourite"))
            rows.append(image)
        return rows
    finally:
        if conn is not None:
            conn.close()


def db_get_memory_ids_for_images(image_ids: Iterable[ImageId]) -> Set[MemoryId]:
    """Get the ids of memories containing any of the given images."""
    ids = list(image_ids)
    if not ids:
        return set()

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        found: Set[MemoryId] = set()
        for start in range(0, len(ids), 500):
            chunk = ids[start : start + 500]
            placeholders = ", ".join("?" * len(chunk))
            cursor.execute(
                f"SELECT DISTINCT memory_id FROM memory_images "
                f"WHERE image_id IN ({placeholders})",
                chunk,
            )
            found.update(row[0] for row in cursor.fetchall())
        return found
    finally:
        if conn is not None:
            conn.close()
