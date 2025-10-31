import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config.settings import DATABASE_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    SQLite connection context manager with all integrity constraints enforced.

    - Enables all major relational integrity PRAGMAs
    - Works for both single and multi-step transactions
    - Automatically commits on success or rolls back on failure
    """
    conn = sqlite3.connect(DATABASE_PATH)

    # --- Strict enforcement of all relational and logical rules ---
    conn.execute("PRAGMA foreign_keys = ON;")  # Enforce FK constraints
    conn.execute("PRAGMA ignore_check_constraints = OFF;")  # Enforce CHECK constraints
    conn.execute("PRAGMA recursive_triggers = ON;")  # Allow nested triggers
    conn.execute("PRAGMA defer_foreign_keys = OFF;")  # Immediate FK checking
    conn.execute("PRAGMA case_sensitive_like = ON;")  # Make LIKE case-sensitive

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
