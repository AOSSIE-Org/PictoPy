import json
import os
import sqlite3
import tempfile
from typing import Any, Dict, Iterator, List, Tuple
from unittest.mock import patch

import pytest

from app.database.metadata import (
    db_create_metadata_table,
    db_get_metadata,
    db_update_metadata,
)

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the metadata DB module at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.metadata.DATABASE_PATH", db_path)

    db_create_metadata_table()

    yield db_path

    os.unlink(db_path)


def stored_rows(db_path: str) -> List[Tuple[str]]:
    """Read the raw metadata rows straight from the table."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT metadata FROM metadata").fetchall()
    conn.close()
    return rows


def write_raw(db_path: str, sql: str, params: Tuple[Any, ...] = ()) -> None:
    """Run a statement against the metadata table and commit it."""
    conn = sqlite3.connect(db_path)
    conn.execute(sql, params)
    conn.commit()
    conn.close()


# ##############################
# Table creation
# ##############################


class TestCreateMetadataTable:
    def test_seeds_a_single_empty_row(self, test_db):
        assert stored_rows(test_db) == [("{}",)]
        assert db_get_metadata() == {}

    def test_preserves_existing_metadata(self, test_db):
        expected: Dict[str, Any] = {"user_preferences": {"YOLO_model_size": "medium"}}
        assert db_update_metadata(expected) is True

        db_create_metadata_table()  # re-running must not reseed the row

        assert len(stored_rows(test_db)) == 1
        assert db_get_metadata() == expected

    def test_survives_a_connection_failure(self):
        """connect() failing leaves conn as None, so the finally must no-op."""
        with patch(
            "app.database.metadata.sqlite3.connect", side_effect=sqlite3.Error("fail")
        ):
            with pytest.raises(sqlite3.Error):
                db_create_metadata_table()


# ##############################
# Reading metadata
# ##############################


class TestGetMetadata:
    def test_returns_none_without_a_row(self, test_db):
        write_raw(test_db, "DELETE FROM metadata")
        assert db_get_metadata() is None

    def test_returns_none_for_blank_metadata(self, test_db):
        write_raw(test_db, "UPDATE metadata SET metadata = ?", ("",))
        assert db_get_metadata() is None

    def test_returns_none_for_invalid_json(self, test_db):
        write_raw(test_db, "UPDATE metadata SET metadata = ?", ("{invalid-json",))
        assert db_get_metadata() is None


# ##############################
# Updating metadata
# ##############################


class TestUpdateMetadata:
    def test_stores_nested_values(self, test_db):
        expected: Dict[str, Any] = {
            "user_preferences": {"YOLO_model_size": "nano", "GPU_Acceleration": False},
            "recent_folders": ["photos", "archives"],
            "version": 2,
        }
        assert db_update_metadata(expected) is True
        assert db_get_metadata() == expected

    def test_replaces_the_previous_row(self, test_db):
        assert db_update_metadata({"old": True}) is True
        assert db_update_metadata({"new": True, "count": 3}) is True

        rows = stored_rows(test_db)
        assert len(rows) == 1
        assert json.loads(rows[0][0]) == {"new": True, "count": 3}

    def test_accepts_a_caller_supplied_cursor(self, test_db):
        expected = {"bulk_update": True}

        conn = sqlite3.connect(test_db)
        try:
            assert db_update_metadata(expected, conn.cursor()) is True
            conn.commit()  # the helper leaves committing to the caller
        finally:
            conn.close()

        assert db_get_metadata() == expected

    def test_rolls_back_when_serialization_fails(self, test_db):
        assert db_update_metadata({"safe": True}) is True

        with pytest.raises(TypeError):
            db_update_metadata({"bad": object()})

        assert db_get_metadata() == {"safe": True}

    def test_caller_cursor_failure_is_left_to_the_caller(self, test_db):
        """On failure with a caller's cursor the helper must not roll back --
        the caller owns the transaction."""
        conn = sqlite3.connect(test_db)
        try:
            cursor = conn.cursor()
            assert db_update_metadata({"safe": True}, cursor) is True

            with pytest.raises(TypeError):
                db_update_metadata({"bad": object()}, cursor)

            # The earlier write survived, so the caller can still commit it
            conn.commit()
        finally:
            conn.close()

        assert db_get_metadata() == {"safe": True}
