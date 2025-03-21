from __future__ import annotations

import sqlite3
import numpy as np
import json
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from contextlib import contextmanager
from app.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

def create_faces_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                embeddings TEXT,
                FOREIGN KEY (image_id) REFERENCES image_id_mapping(id) ON DELETE CASCADE
            )
        """
        )
        conn.commit()

def insert_face_embeddings(image_path, embeddings):
    from app.database.images import get_id_from_path

    with get_db_connection() as conn:
        cursor = conn.cursor()

        image_id = get_id_from_path(image_path)
        if image_id is None:
            raise ValueError(f"Image '{image_path}' not found in the database")
        
        # Continue with the rest of the function
        # (This part was missing in the merge conflict)

def init_face_db():
    """Initialize the faces database with required tables."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add index for faster queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_path 
            ON face_embeddings(image_path)
        """)
        conn.commit()

def store_face_embeddings_batch(
    image_paths: List[str],
    embeddings: List[np.ndarray]
) -> None:
    """
    Store multiple face embeddings in a single transaction.
    
    Args:
        image_paths: List of image paths
        embeddings: List of corresponding embeddings
    """
    if len(image_paths) != len(embeddings):
        raise ValueError("Number of paths must match number of embeddings")
        
    with get_db_connection() as conn:
        try:
            conn.executemany(
                "INSERT INTO face_embeddings (image_path, embedding) VALUES (?, ?)",
                [
                    (path, embedding.tobytes())
                    for path, embedding in zip(image_paths, embeddings)
                ]
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            raise

def store_face_embedding(image_path: str, embedding: np.ndarray) -> None:
    """
    Store a single face embedding.
    
    Args:
        image_path: Path to the image
        embedding: Face embedding vector
    """
    store_face_embeddings_batch([image_path], [embedding])

def get_face_embeddings(image_path: str) -> List[np.ndarray]:
    """
    Retrieve all face embeddings for an image.
    
    Args:
        image_path: Path to the image
        
    Returns:
        List of face embeddings
    """
    # First try the new performance-optimized table
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT embedding FROM face_embeddings WHERE image_path = ?",
            (image_path,)
        )
        results = cursor.fetchall()
        if results:
            return [
                np.frombuffer(row[0], dtype=np.float32)
                for row in results
            ]
    
    # Fall back to the old table structure if needed
    from app.database.images import get_id_from_path

    with get_db_connection() as conn:
        cursor = conn.cursor()

        image_id = get_id_from_path(image_path)
        if image_id is None:
            return None

        cursor.execute(
            """
            SELECT embeddings FROM faces
            WHERE image_id = ?
        """,
            (image_id,),
        )

        result = cursor.fetchone()

        if result:
            embeddings_json = result[0]
            embeddings = np.array(json.loads(embeddings_json))
            return [embeddings]
        else:
            return []

def get_all_face_embeddings() -> List[Tuple[str, np.ndarray]]:
    """
    Retrieve all face embeddings from the database.
    
    Returns:
        List of tuples containing (image_path, embedding)
    """
    # First try the new performance-optimized table
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT image_path, embedding FROM face_embeddings"
        )
        results = cursor.fetchall()
        if results:
            return [
                (row[0], np.frombuffer(row[1], dtype=np.float32))
                for row in results
            ]
    
    # Fall back to the old table structure if needed
    from app.database.images import get_path_from_id

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT image_id, embeddings FROM faces
            """
        )

        results = cursor.fetchall()
        all_embeddings = []
        for image_id, embeddings_json in results:
            image_path = get_path_from_id(image_id)
            embeddings = np.array(json.loads(embeddings_json))
            all_embeddings.append((image_path, embeddings))
        
        return all_embeddings

def clear_face_embeddings() -> None:
    """Clear all face embeddings from the database."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM face_embeddings")
        conn.commit()

def delete_face_embeddings(image_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))
        conn.commit()

def cleanup_face_embeddings():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT image_id FROM faces")
        face_image_ids = set(row[0] for row in cursor.fetchall())

        cursor.execute("SELECT id FROM image_id_mapping")
        valid_image_ids = set(row[0] for row in cursor.fetchall())

        orphaned_ids = face_image_ids - valid_image_ids

        for orphaned_id in orphaned_ids:
            cursor.execute("DELETE FROM faces WHERE image_id = ?", (orphaned_id,))

        conn.commit()
