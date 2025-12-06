
import sqlite3
import pickle
import numpy as np
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
DB_PATH = "pictopy.db" # Assuming standard path, configurable

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_create_embeddings_table():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS image_embeddings (
                image_path TEXT PRIMARY KEY,
                embedding BLOB
            )
        ''')
        conn.commit()
        logger.info("Created image_embeddings table")
    except Exception as e:
        logger.error(f"Error creating embeddings table: {e}")
    finally:
        conn.close()

def db_save_embedding(image_path, embedding):
    conn = get_db_connection()
    try:
        # Store numpy array as bytes
        blob = pickle.dumps(embedding)
        conn.execute('''
            INSERT OR REPLACE INTO image_embeddings (image_path, embedding)
            VALUES (?, ?)
        ''', (image_path, blob))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving embedding for {image_path}: {e}")
    finally:
        conn.close()

def db_get_all_embeddings():
    """Returns a dict {image_path: embedding_vector}"""
    conn = get_db_connection()
    results = {}
    try:
        cursor = conn.execute("SELECT image_path, embedding FROM image_embeddings")
        for row in cursor:
            path = row['image_path']
            blob = row['embedding']
            if blob:
                results[path] = pickle.loads(blob)
    except Exception as e:
        logger.error(f"Error fetching embeddings: {e}")
    finally:
        conn.close()
    return results
