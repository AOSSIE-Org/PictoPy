from __future__ import annotations

import sqlite3
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Union
from contextlib import contextmanager

from app.config.settings import FACES_DATABASE_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(FACES_DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def create_faces_table():
    """Initialize the faces database with required tables."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Add index for faster queries
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_image_path 
            ON face_embeddings(image_path)
        """
        )
        conn.commit()


def cleanup_face_embeddings(batch_size: int = 1000) -> int:
    cleaned = 0
    with get_db_connection() as conn:
        while True:
            cursor = conn.execute(
                """SELECT DISTINCT image_path 
                   FROM face_embeddings 
                   LIMIT ?""",
                (batch_size,),
            )
            batch = cursor.fetchall()
            if not batch:
                break

            for (path,) in batch:
                if not Path(path).exists():
                    conn.execute(
                        "DELETE FROM face_embeddings WHERE image_path = ?", (path,)
                    )
                    cleaned += 1

            conn.commit()

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} orphaned face embedding entries")
    return cleaned


def insert_face_embeddings(
    image_path: Union[str, Path], embeddings: List[np.ndarray]
) -> None:
    """
    Insert face embeddings for an image into the database.

    Args:
        image_path: Path to the image file
        embeddings: List of face embeddings as numpy arrays
    """
    if not embeddings:
        return

    # Convert path to string if it's a Path object
    image_path_str = str(image_path)

    with get_db_connection() as conn:
        try:
            # Delete any existing embeddings for this image
            conn.execute(
                "DELETE FROM face_embeddings WHERE image_path = ?", (image_path_str,)
            )

            # Insert new embeddings
            conn.executemany(
                "INSERT INTO face_embeddings (image_path, embedding) VALUES (?, ?)",
                [(image_path_str, embedding.tobytes()) for embedding in embeddings],
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error while inserting face embeddings: {str(e)}")
            raise


def get_face_embeddings(image_path: Union[str, Path]) -> List[np.ndarray]:
    """
    Retrieve face embeddings for an image from the database.

    Args:
        image_path: Path to the image file

    Returns:
        List of face embeddings as numpy arrays
    """
    image_path_str = str(image_path)

    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT embedding FROM face_embeddings WHERE image_path = ?",
            (image_path_str,),
        )
        rows = cursor.fetchall()

        return [
            np.frombuffer(embedding_bytes[0], dtype=np.float32)
            for embedding_bytes in rows
        ]


def get_all_face_embeddings() -> List[dict]:
    """
    Retrieve all face embeddings from the database.

    Returns:
        List of dictionaries containing image paths and their embeddings
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT image_path, GROUP_CONCAT(embedding) FROM face_embeddings GROUP BY image_path"
        )
        rows = cursor.fetchall()

        result = []
        for image_path, embeddings_blob in rows:
            if embeddings_blob:
                embeddings = [
                    np.frombuffer(embedding, dtype=np.float32)
                    for embedding in embeddings_blob.split(",")
                ]
                result.append({"image_path": image_path, "embeddings": embeddings})

        return result


def batch_insert_face_embeddings(
    embeddings_batch: List[Tuple[str, List[np.ndarray]]], batch_size: int = 1000
) -> None:
    """
    Insert multiple face embeddings in batch for better performance.

    Args:
        embeddings_batch: List of tuples containing (image_path, embeddings)
        batch_size: Number of embeddings to insert in each batch
    """
    with get_db_connection() as conn:
        try:
            all_values = []
            for image_path, embeddings in embeddings_batch:
                all_values.extend(
                    [(str(image_path), embedding.tobytes()) for embedding in embeddings]
                )

            for i in range(0, len(all_values), batch_size):
                chunk = all_values[i : i + batch_size]
                conn.executemany(
                    "INSERT INTO face_embeddings (image_path, embedding) VALUES (?, ?)",
                    chunk,
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Batch insert error: {str(e)}")
            raise


def optimize_database() -> None:
    """Optimize the database for better performance."""
    with get_db_connection() as conn:
        conn.execute("PRAGMA optimize")
        conn.execute("ANALYZE face_embeddings")
        conn.execute("VACUUM")


def get_database_stats() -> dict:
    """Get statistics about the face embeddings database."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM face_embeddings")
        total_embeddings = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(DISTINCT image_path) FROM face_embeddings")
        total_images = cursor.fetchone()[0]

        return {
            "total_embeddings": total_embeddings,
            "total_images": total_images,
            "database_size_bytes": Path(FACES_DATABASE_PATH).stat().st_size,
        }
