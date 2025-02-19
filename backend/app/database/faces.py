from __future__ import annotations

import sqlite3
import numpy as np
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
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT embedding FROM face_embeddings WHERE image_path = ?",
            (image_path,)
        )
        return [
            np.frombuffer(row[0], dtype=np.float32)
            for row in cursor.fetchall()
        ]

def get_all_face_embeddings() -> List[Tuple[str, np.ndarray]]:
    """
    Retrieve all face embeddings from the database.
    
    Returns:
        List of tuples containing (image_path, embedding)
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT image_path, embedding FROM face_embeddings"
        )
        return [
            (row[0], np.frombuffer(row[1], dtype=np.float32))
            for row in cursor.fetchall()
        ]

def clear_face_embeddings() -> None:
    """Clear all face embeddings from the database."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM face_embeddings")
        conn.commit()
