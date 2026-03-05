import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config.settings import DATABASE_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DATABASE_PATH)

    # VERY IMPORTANT
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA ignore_check_constraints = OFF;")
    conn.execute("PRAGMA recursive_triggers = ON;")
    conn.execute("PRAGMA defer_foreign_keys = OFF;")
    conn.execute("PRAGMA case_sensitive_like = ON;")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()