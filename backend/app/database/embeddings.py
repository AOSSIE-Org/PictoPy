"""
Persistent storage for per-image semantic embeddings.

Each image is represented by a float32 numpy vector stored as raw bytes
(BLOB) inside the existing PictoPy SQLite database.  The table is linked
to the ``images`` table via a CASCADE-delete foreign key so embeddings are
automatically purged when an image is removed.

Public surface
--------------
db_create_embeddings_table()          – called once on startup
db_upsert_embedding(image_id, vec)    – insert or replace
db_get_embedding(image_id)            – single lookup
db_get_all_embeddings()               – bulk load for index rebuild
db_delete_embedding(image_id)         – explicit removal
db_get_indexed_image_ids()            – list of indexed IDs
db_embedding_exists(image_id)         – cheap existence check
"""

import sqlite3
from typing import List, Optional, Tuple

import numpy as np

from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def db_create_embeddings_table() -> None:
    """Create the ``image_embeddings`` table if it does not already exist."""
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS image_embeddings (
                image_id   TEXT    PRIMARY KEY,
                embedding  BLOB    NOT NULL,
                dim        INTEGER NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_image_embeddings_image_id
            ON image_embeddings(image_id)
            """
        )
        conn.commit()
        logger.debug("image_embeddings table is ready")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def db_upsert_embedding(image_id: str, embedding: np.ndarray) -> None:
    """
    Insert or replace the embedding for *image_id*.

    Parameters
    ----------
    image_id :
        The UUID string used as primary key in the ``images`` table.
    embedding :
        1-D float32 numpy array.  Converted to float32 internally if needed.
    """
    vec = embedding.astype(np.float32)
    blob = vec.tobytes()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO image_embeddings (image_id, embedding, dim, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(image_id) DO UPDATE SET
                embedding  = excluded.embedding,
                dim        = excluded.dim,
                updated_at = excluded.updated_at
            """,
            (image_id, blob, len(vec)),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to upsert embedding for image %s", image_id)
        raise
    finally:
        conn.close()


def db_delete_embedding(image_id: str) -> None:
    """Remove the embedding row for *image_id* (no-op if absent)."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM image_embeddings WHERE image_id = ?", (image_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


def db_get_embedding(image_id: str) -> Optional[np.ndarray]:
    """
    Return the stored embedding for *image_id*, or ``None`` if not indexed.
    """
    conn = _connect()
    try:
        cursor = conn.execute(
            "SELECT embedding, dim FROM image_embeddings WHERE image_id = ?",
            (image_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        blob, dim = row
        vec = np.frombuffer(blob, dtype=np.float32).copy()
        return vec if len(vec) == dim else None
    finally:
        conn.close()


def db_get_all_embeddings() -> List[Tuple[str, np.ndarray]]:
    """
    Load every stored embedding in a single pass.

    Returns
    -------
    list of (image_id, float32 vector) tuples – order is unspecified.
    """
    conn = _connect()
    try:
        cursor = conn.execute("SELECT image_id, embedding, dim FROM image_embeddings")
        results: List[Tuple[str, np.ndarray]] = []
        for image_id, blob, dim in cursor.fetchall():
            vec = np.frombuffer(blob, dtype=np.float32).copy()
            if len(vec) == dim:
                results.append((image_id, vec))
            else:
                logger.warning(
                    "Skipping corrupt embedding for image %s (stored dim=%d, actual=%d)",
                    image_id,
                    dim,
                    len(vec),
                )
        return results
    finally:
        conn.close()


def db_get_indexed_image_ids() -> List[str]:
    """Return the list of image_ids that have a stored embedding."""
    conn = _connect()
    try:
        cursor = conn.execute("SELECT image_id FROM image_embeddings")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def db_embedding_exists(image_id: str) -> bool:
    """Return ``True`` if an embedding is already stored for *image_id*."""
    conn = _connect()
    try:
        cursor = conn.execute(
            "SELECT 1 FROM image_embeddings WHERE image_id = ? LIMIT 1",
            (image_id,),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()
