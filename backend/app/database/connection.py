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

    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout
            conn.execute("PRAGMA busy_timeout=30000")
            # Enable foreign keys for data integrity
            conn.execute("PRAGMA foreign_keys=ON")

            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
            break

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                continue
            else:
                raise e
