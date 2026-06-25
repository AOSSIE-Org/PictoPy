import json
import sqlite3

import pytest

from app.database import metadata as metadata_db


@pytest.fixture()
def metadata_database(tmp_path, monkeypatch):
    db_path = tmp_path / "metadata.sqlite3"
    monkeypatch.setattr(metadata_db, "DATABASE_PATH", str(db_path))
    return db_path


# Validates that metadata table creation inserts a default empty metadata row.
def test_create_metadata_table_initializes_empty_metadata(metadata_database):
    metadata_db.db_create_metadata_table()

    with sqlite3.connect(str(metadata_database)) as conn:
        rows = conn.execute("SELECT metadata FROM metadata").fetchall()

    assert rows == [("{}",)]
    assert metadata_db.db_get_metadata() == {}


# Validates that creating the metadata table again does not overwrite existing metadata.
def test_create_metadata_table_preserves_existing_metadata(metadata_database):
    metadata_db.db_create_metadata_table()
    expected_metadata = {"user_preferences": {"YOLO_model_size": "medium"}}

    assert metadata_db.db_update_metadata(expected_metadata) is True
    metadata_db.db_create_metadata_table()

    with sqlite3.connect(str(metadata_database)) as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM metadata").fetchone()[0]

    assert row_count == 1
    assert metadata_db.db_get_metadata() == expected_metadata


# Validates that metadata retrieval returns None when the table has no metadata row.
def test_get_metadata_returns_none_when_no_row_exists(metadata_database):
    metadata_db.db_create_metadata_table()

    with sqlite3.connect(str(metadata_database)) as conn:
        conn.execute("DELETE FROM metadata")

    assert metadata_db.db_get_metadata() is None


# Validates that blank metadata content is treated as missing metadata.
def test_get_metadata_returns_none_for_blank_metadata(metadata_database):
    metadata_db.db_create_metadata_table()

    with sqlite3.connect(str(metadata_database)) as conn:
        conn.execute("UPDATE metadata SET metadata = ?", ("",))

    assert metadata_db.db_get_metadata() is None


# Validates that invalid JSON in the metadata row is handled as missing metadata.
def test_get_metadata_returns_none_for_invalid_json(metadata_database):
    metadata_db.db_create_metadata_table()

    with sqlite3.connect(str(metadata_database)) as conn:
        conn.execute("UPDATE metadata SET metadata = ?", ("{invalid-json",))

    assert metadata_db.db_get_metadata() is None


# Validates that updating metadata stores nested JSON-compatible values.
def test_update_metadata_stores_nested_values(metadata_database):
    metadata_db.db_create_metadata_table()
    expected_metadata = {
        "user_preferences": {"YOLO_model_size": "nano", "GPU_Acceleration": False},
        "recent_folders": ["photos", "archives"],
        "version": 2,
    }

    assert metadata_db.db_update_metadata(expected_metadata) is True

    assert metadata_db.db_get_metadata() == expected_metadata


# Validates that updating metadata replaces the previous row instead of appending another row.
def test_update_metadata_replaces_existing_metadata_row(metadata_database):
    metadata_db.db_create_metadata_table()
    old_metadata = {"old": True}
    new_metadata = {"new": True, "count": 3}

    assert metadata_db.db_update_metadata(old_metadata) is True
    assert metadata_db.db_update_metadata(new_metadata) is True

    with sqlite3.connect(str(metadata_database)) as conn:
        rows = conn.execute("SELECT metadata FROM metadata").fetchall()

    assert len(rows) == 1
    assert json.loads(rows[0][0]) == new_metadata


# Validates that metadata can be updated through an existing database cursor.
def test_update_metadata_with_existing_cursor(metadata_database):
    metadata_db.db_create_metadata_table()
    expected_metadata = {"bulk_update": True}

    conn = sqlite3.connect(str(metadata_database))
    try:
        cursor = conn.cursor()
        assert metadata_db.db_update_metadata(expected_metadata, cursor) is True
        conn.commit()
    finally:
        conn.close()

    assert metadata_db.db_get_metadata() == expected_metadata


# Validates that update failures roll back without deleting previous metadata.
def test_update_metadata_rolls_back_when_json_serialization_fails(metadata_database):
    metadata_db.db_create_metadata_table()
    original_metadata = {"safe": True}

    assert metadata_db.db_update_metadata(original_metadata) is True

    with pytest.raises(TypeError):
        metadata_db.db_update_metadata({"bad": object()})

    assert metadata_db.db_get_metadata() == original_metadata