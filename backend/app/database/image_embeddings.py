from typing import List, Tuple
import numpy as np
from app.database.images import _connect


def db_create_image_embeddings_table():
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_embeddings (
                image_id TEXT PRIMARY KEY,
                model_version TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_image_embeddings_model_version "
            "ON image_embeddings(model_version)"
        )
        # scored_signature: which vocabulary/label state this image's semantic
        # scores were computed against (NULL = never scored). Guarded ALTER
        # for databases that predate the column.
        cursor.execute("PRAGMA table_info(image_embeddings)")
        if "scored_signature" not in {row[1] for row in cursor.fetchall()}:
            cursor.execute(
                "ALTER TABLE image_embeddings ADD COLUMN scored_signature TEXT"
            )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_upsert_image_embeddings(rows: List[Tuple[str, str, np.ndarray]]):
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        # Convert each embedding
        db_rows = [
            (
                image_id,
                model_version,
                np.ascontiguousarray(embedding, dtype=np.float32).tobytes(),
            )
            for image_id, model_version, embedding in rows
        ]

        cursor.executemany(
            """
            INSERT INTO image_embeddings (image_id, model_version, embedding)
            VALUES (?, ?, ?)
            ON CONFLICT(image_id) DO UPDATE SET
                model_version = excluded.model_version,
                embedding = excluded.embedding,
                created_at = CURRENT_TIMESTAMP
            """,
            db_rows,
        )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_get_all_embeddings(model_version: str) -> Tuple[List[str], np.ndarray]:
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT image_id, embedding FROM image_embeddings
            WHERE model_version = ?
            """,
            (model_version,),
        )

        rows = cursor.fetchall()
        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        image_ids = []
        embeddings_list = []

        for image_id, blob in rows:
            image_ids.append(image_id)
            embeddings_list.append(np.frombuffer(blob, dtype=np.float32))

        matrix = np.vstack(embeddings_list)
        return image_ids, matrix
    finally:
        if conn:
            conn.close()


def db_get_embeddings_needing_scoring(
    model_version: str, signature: str, limit: int
) -> Tuple[List[str], np.ndarray]:
    """Embeddings whose semantic scores are missing or from another
    vocabulary/label state. Returns up to `limit` (image_ids, matrix)."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT image_id, embedding FROM image_embeddings
            WHERE model_version = ? AND IFNULL(scored_signature, '') != ?
            LIMIT ?
            """,
            (model_version, signature, limit),
        )
        rows = cursor.fetchall()
        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        image_ids = [image_id for image_id, _ in rows]
        matrix = np.vstack([np.frombuffer(blob, dtype=np.float32) for _, blob in rows])
        return image_ids, matrix
    finally:
        if conn:
            conn.close()


def db_count_embeddings(model_version: str | None = None) -> int:
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        if model_version is not None:
            cursor.execute(
                "SELECT COUNT(*) FROM image_embeddings WHERE model_version = ?",
                (model_version,),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM image_embeddings")

        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        if conn:
            conn.close()
