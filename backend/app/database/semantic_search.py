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

def db_create_indexing_status_table() -> None:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_indexing_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active BOOLEAN DEFAULT 0,
                current INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                error TEXT
            )
            """
        )
        # Ensure initial row exists
        cursor.execute("INSERT OR IGNORE INTO semantic_indexing_status (id, is_active, current, total, error) VALUES (1, 0, 0, 0, NULL)")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating status table: {e}")
        raise e
    finally:
        conn.close()

def db_update_indexing_status(is_active: bool = None, current: int = None, total: int = None, error: str = None) -> None:
    conn = _connect()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if current is not None:
            updates.append("current = ?")
            params.append(current)
        if total is not None:
            updates.append("total = ?")
            params.append(total)
        
        # Explicitly handle error being None vs not provided
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        elif 'error' in updates: # This won't happen here but logically for clear
            pass

        if not updates:
            return

        query = f"UPDATE semantic_indexing_status SET {', '.join(updates)} WHERE id = 1"
        cursor.execute(query, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating indexing status: {e}")
    finally:
        conn.close()

def db_get_indexing_status() -> dict:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT is_active, current, total, error FROM semantic_indexing_status WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "is_active": bool(row[0]),
                "current": row[1],
                "total": row[2],
                "error": row[3]
            }
        return {"is_active": False, "current": 0, "total": 0, "error": None}
    finally:
        conn.close()
