import sqlite3
import time
from contextlib import contextmanager
from typing import Generator
from app.config.settings import DATABASE_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections with proper error handling and retries.
    Provides a shared connection for all database operations within the context.
    Automatically commits on success or rolls back on failure.

    Usage:
        with get_db_connection() as conn:
            # All database operations using conn will be in the same transaction
            db_function_1(conn=conn)
            db_function_2(conn=conn)
            # Transaction commits automatically if no exceptions

    Yields:
        sqlite3.Connection: Database connection with transaction started

    Raises:
        Exception: Re-raises any exception that occurs during the transaction
    """
    max_retries = 3
    retry_delay = 0.1
    conn = None
    last_err = None

    # Retry only the connection establishment, not the transaction execution
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout
            conn.execute("PRAGMA busy_timeout=30000")
            # Enable foreign keys for data integrity
            conn.execute("PRAGMA foreign_keys=ON")
            last_err = None
            break
        except sqlite3.OperationalError as e:
            last_err = e
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                continue
            raise

    if conn is None:
        # Shouldn't happen, but keep a clear failure path
        raise last_err or RuntimeError("Failed to establish database connection")

    # Now yield the connection exactly once
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
