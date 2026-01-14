import sqlite3
import numpy as np
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)

def db_create_embeddings_table() -> None:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_embeddings (
                image_id TEXT PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating embeddings table: {e}")
        raise e
    finally:
        conn.close()

def db_upsert_embedding(image_id: str, embedding: np.ndarray) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    try:
        # Convert numpy array to bytes
        embedding_bytes = embedding.astype(np.float32).tobytes()
        cursor.execute(
            """
            INSERT OR REPLACE INTO image_embeddings (image_id, embedding)
            VALUES (?, ?)
            """,
            (image_id, embedding_bytes)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error upserting embedding for {image_id}: {e}")
        return False
    finally:
        conn.close()

def db_get_all_embeddings() -> dict:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_id, embedding FROM image_embeddings")
        results = cursor.fetchall()
        
        embeddings = {}
        for image_id, embedding_blob in results:
            # Convert bytes back to numpy array
            embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
            embeddings[image_id] = embedding_array
            
        return embeddings
    except Exception as e:
        logger.error(f"Error fetching embeddings: {e}")
        return {}
    finally:
        conn.close()

def db_get_missing_embeddings_image_ids() -> list:
    """Get IDs of images that don't have embeddings yet."""
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT i.id 
            FROM images i 
            LEFT JOIN image_embeddings ie ON i.id = ie.image_id 
            WHERE ie.image_id IS NULL
            """
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
