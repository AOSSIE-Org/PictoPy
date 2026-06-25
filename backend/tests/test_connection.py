import sqlite3
import pytest
from unittest.mock import patch

from app.database.connection import get_db_connection


def test_get_db_connection_commits_on_success(tmp_path):
    db_path = tmp_path / "test.db"

    with patch("app.database.connection.DATABASE_PATH", str(db_path)):
        with get_db_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS test")
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))

        # reopen DB to check commit happened
        conn = sqlite3.connect(db_path)
        result = conn.execute("SELECT name FROM test").fetchone()
        conn.close()

    assert result[0] == "Alice"


def test_get_db_connection_rolls_back_on_exception(tmp_path):
    db_path = tmp_path / "test.db"

    with patch("app.database.connection.DATABASE_PATH", str(db_path)):
        # Create table first and commit successfully
        with get_db_connection() as conn:
            conn.execute(
                "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
            )

        # Insert data, then raise error
        with pytest.raises(ValueError):
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO test (name) VALUES (?)",
                    ("Bob",),
                )
                raise ValueError("fail")

        # Check Bob was rolled back
        conn = sqlite3.connect(db_path)
        result = conn.execute("SELECT name FROM test").fetchone()
        conn.close()
    assert result is None

def test_get_db_connection_enables_pragmas(tmp_path):
    db_path = tmp_path / "test.db"

    with patch("app.database.connection.DATABASE_PATH", str(db_path)):
        with get_db_connection() as conn:
            foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            ignore_check = conn.execute("PRAGMA ignore_check_constraints").fetchone()[0]
            recursive_triggers = conn.execute("PRAGMA recursive_triggers").fetchone()[0]

    assert foreign_keys == 1
    assert ignore_check == 0
    assert recursive_triggers == 1