import sqlite3

import pytest

from app.database import yolo_mapping as yolo_mapping_db


@pytest.fixture()
def yolo_database(tmp_path, monkeypatch):
    db_path = tmp_path / "yolo_mapping.sqlite3"
    monkeypatch.setattr(yolo_mapping_db, "DATABASE_PATH", str(db_path))
    return db_path


def fetch_mappings(db_path):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT class_id, name FROM mappings ORDER BY class_id"
        ).fetchall()


# Validates that YOLO class table creation stores each class name with its index.
def test_create_yolo_classes_table_inserts_class_names(yolo_database, monkeypatch):
    monkeypatch.setattr(yolo_mapping_db, "class_names", ["person", "bicycle", "car"])

    yolo_mapping_db.db_create_YOLO_classes_table()

    assert fetch_mappings(yolo_database) == [
        (0, "person"),
        (1, "bicycle"),
        (2, "car"),
    ]


# Validates that rerunning table creation does not duplicate existing class mappings.
def test_create_yolo_classes_table_is_idempotent(yolo_database, monkeypatch):
    monkeypatch.setattr(yolo_mapping_db, "class_names", ["person", "car"])

    yolo_mapping_db.db_create_YOLO_classes_table()
    yolo_mapping_db.db_create_YOLO_classes_table()

    assert fetch_mappings(yolo_database) == [(0, "person"), (1, "car")]


# Validates that existing class IDs are replaced when class names change.
def test_create_yolo_classes_table_replaces_existing_class_names(
    yolo_database, monkeypatch
):
    monkeypatch.setattr(yolo_mapping_db, "class_names", ["old-person", "old-car"])
    yolo_mapping_db.db_create_YOLO_classes_table()

    monkeypatch.setattr(yolo_mapping_db, "class_names", ["person", "car"])
    yolo_mapping_db.db_create_YOLO_classes_table()

    assert fetch_mappings(yolo_database) == [(0, "person"), (1, "car")]


# Validates that table creation succeeds when no YOLO classes are configured.
def test_create_yolo_classes_table_handles_empty_class_list(yolo_database, monkeypatch):
    monkeypatch.setattr(yolo_mapping_db, "class_names", [])

    yolo_mapping_db.db_create_YOLO_classes_table()

    assert fetch_mappings(yolo_database) == []


# Validates that duplicate class names can be stored under different class IDs.
def test_create_yolo_classes_table_allows_duplicate_names_with_distinct_ids(
    yolo_database, monkeypatch
):
    monkeypatch.setattr(yolo_mapping_db, "class_names", ["person", "person"])

    yolo_mapping_db.db_create_YOLO_classes_table()

    assert fetch_mappings(yolo_database) == [(0, "person"), (1, "person")]