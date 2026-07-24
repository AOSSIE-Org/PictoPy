import os
import sqlite3
import tempfile
from typing import Iterator, List, Tuple
from unittest.mock import patch

import pytest

from app.database.yolo_mapping import db_create_YOLO_classes_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the YOLO mapping DB module at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    yield db_path

    os.unlink(db_path)


def set_class_names(monkeypatch: pytest.MonkeyPatch, names: List[str]) -> None:
    """Swap the YOLO vocabulary the table is seeded from."""
    monkeypatch.setattr("app.database.yolo_mapping.class_names", names)


def fetch_mappings(db_path: str) -> List[Tuple[int, str]]:
    """Read every mappings row, ordered by class_id."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT class_id, name FROM mappings ORDER BY class_id"
    ).fetchall()
    conn.close()
    return rows


# ##############################
# Table creation
# ##############################


class TestCreateYOLOClassesTable:
    def test_inserts_class_names_by_index(self, test_db, monkeypatch):
        set_class_names(monkeypatch, ["person", "bicycle", "car"])

        db_create_YOLO_classes_table()

        assert fetch_mappings(test_db) == [(0, "person"), (1, "bicycle"), (2, "car")]

    def test_is_idempotent(self, test_db, monkeypatch):
        set_class_names(monkeypatch, ["person", "car"])

        db_create_YOLO_classes_table()
        db_create_YOLO_classes_table()

        assert fetch_mappings(test_db) == [(0, "person"), (1, "car")]

    def test_replaces_renamed_classes(self, test_db, monkeypatch):
        set_class_names(monkeypatch, ["old-person", "old-car"])
        db_create_YOLO_classes_table()

        # Same ids, new names -> INSERT OR REPLACE overwrites in place
        set_class_names(monkeypatch, ["person", "car"])
        db_create_YOLO_classes_table()

        assert fetch_mappings(test_db) == [(0, "person"), (1, "car")]

    def test_handles_an_empty_class_list(self, test_db, monkeypatch):
        set_class_names(monkeypatch, [])

        db_create_YOLO_classes_table()

        assert fetch_mappings(test_db) == []

    def test_allows_duplicate_names_with_distinct_ids(self, test_db, monkeypatch):
        set_class_names(monkeypatch, ["person", "person"])

        db_create_YOLO_classes_table()

        assert fetch_mappings(test_db) == [(0, "person"), (1, "person")]

    def test_survives_a_connection_failure(self):
        """connect() failing leaves conn as None, so the finally must no-op."""
        with patch(
            "app.database.yolo_mapping.sqlite3.connect",
            side_effect=sqlite3.Error("fail"),
        ):
            with pytest.raises(sqlite3.Error):
                db_create_YOLO_classes_table()
