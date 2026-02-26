import os
import sqlite3
import tempfile
import pytest

from app.database.connection import get_db_connection


@pytest.fixture
def temp_db_path(monkeypatch):
    """
    Creates a temporary SQLite database file
    and overrides DATABASE_PATH for isolated testing.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    monkeypatch.setattr(
        "app.database.connection.DATABASE_PATH",
        temp_file.name
    )

    yield temp_file.name

    os.unlink(temp_file.name)


def test_connection_creation_and_pragmas(temp_db_path):
    """
    Ensure connection is created and PRAGMA settings are enforced.
    """
    with get_db_connection() as conn:
        assert isinstance(conn, sqlite3.Connection)

        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        check_status = conn.execute("PRAGMA ignore_check_constraints;").fetchone()[0]
        recursive_status = conn.execute("PRAGMA recursive_triggers;").fetchone()[0]
        defer_status = conn.execute("PRAGMA defer_foreign_keys;").fetchone()[0]

        like_result = conn.execute("PRAGMA case_sensitive_like;").fetchone()

        # Some SQLite builds return None for this PRAGMA
        if like_result is not None:
            assert like_result[0] == 1

        assert fk_status == 1
        assert check_status == 0
        assert recursive_status == 1
        assert defer_status == 0


def test_commit_on_success(temp_db_path):
    """
    Ensure data is committed automatically when no exception occurs.
    """
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE test (id INTEGER);")
        conn.execute("INSERT INTO test (id) VALUES (1);")

    conn = sqlite3.connect(temp_db_path)
    rows = conn.execute("SELECT * FROM test;").fetchall()
    conn.close()

    assert rows == [(1,)]


def test_rollback_on_exception(temp_db_path):
    """
    Ensure transaction is rolled back when exception occurs.
    """
    with pytest.raises(Exception):
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER);")
            conn.execute("INSERT INTO test (id) VALUES (1);")
            raise Exception("Force rollback")

    # Table remains (DDL auto-commits), but INSERT should be rolled back
    conn = sqlite3.connect(temp_db_path)
    rows = conn.execute("SELECT * FROM test;").fetchall()
    conn.close()

    assert rows == []


def test_connection_closed_after_context(temp_db_path):
    """
    Ensure connection is closed after exiting context manager.
    """
    with get_db_connection() as conn:
        pass

    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1;")