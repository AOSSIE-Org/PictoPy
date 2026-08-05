import os
import sqlite3
import tempfile
from typing import Iterator, List, Tuple

import pytest

from app.database.connection import get_db_connection

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the connection helper at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    try:
        monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
        monkeypatch.setattr("app.database.connection.DATABASE_PATH", db_path)

        yield db_path
    finally:
        os.unlink(db_path)


def read_names(db_path: str) -> List[Tuple[str]]:
    """Read every row from the scratch table on a separate connection."""
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT name FROM test").fetchall()
    finally:
        conn.close()


# ##############################
# Transaction handling
# ##############################


class TestGetDbConnection:
    def test_commits_on_success(self, test_db):
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))

        # Visible from a fresh connection, so the commit really happened
        assert read_names(test_db) == [("Alice",)]

    def test_rolls_back_on_exception(self, test_db):
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

        with pytest.raises(ValueError):
            with get_db_connection() as conn:
                conn.execute("INSERT INTO test (name) VALUES (?)", ("Bob",))
                raise ValueError("fail")

        assert read_names(test_db) == []

    def test_closes_the_connection_on_the_way_out(self, test_db):
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

        # The handle is released, so using it again is an error
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


# ##############################
# Pragmas
# ##############################


class TestConnectionPragmas:
    @pytest.mark.parametrize(
        "pragma, expected",
        [
            ("foreign_keys", 1),
            ("ignore_check_constraints", 0),
            ("recursive_triggers", 1),
            ("defer_foreign_keys", 0),
        ],
    )
    def test_enforcement_pragmas_are_set(self, test_db, pragma, expected):
        with get_db_connection() as conn:
            assert conn.execute(f"PRAGMA {pragma}").fetchone()[0] == expected
