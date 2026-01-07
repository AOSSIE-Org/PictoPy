import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config.settings import DATABASE_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    SQLite connection context manager with concurrency optimization and integrity constraints.

    - Enables WAL mode for better concurrent access
    - Configures timeouts and concurrency PRAGMAs
    - Enforces all major relational integrity PRAGMAs
    - Works for both single and multi-step transactions
    - Automatically commits on success or rolls back on failure
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        
        # --- Concurrency and performance optimizations ---
        conn.execute("PRAGMA journal_mode = WAL;")  # Enable WAL mode for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL;")  # Balance safety and performance
        conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY;")  # Store temp tables in memory
        conn.execute("PRAGMA mmap_size = 268435456;")  # 256MB memory-mapped I/O
        conn.execute("PRAGMA busy_timeout = 30000;")  # 30 second timeout for locks
        
        # --- Strict enforcement of all relational and logical rules ---
        conn.execute("PRAGMA foreign_keys = ON;")  # Enforce FK constraints
        conn.execute("PRAGMA ignore_check_constraints = OFF;")  # Enforce CHECK constraints
        conn.execute("PRAGMA defer_foreign_keys = OFF;")  # Immediate FK checking

        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
