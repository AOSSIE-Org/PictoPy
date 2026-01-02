import sqlite3
from app.config.settings import DATABASE_PATH

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def enable_wal_mode():
    """Enable Write-Ahead Logging (WAL) mode for better concurrency."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.commit()
        print("DEBUG: WAL mode enabled.")
    except Exception as e:
        print(f"DEBUG: Failed to enable WAL mode: {e}")
    finally:
        if conn:
            conn.close()
