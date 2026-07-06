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
