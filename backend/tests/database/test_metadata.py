import sqlite3
import json
import pytest

from app.database import metadata


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """
    Create isolated temporary database and patch metadata module
    to use this DB instead of real project DB.
    """
    db_file = tmp_path / "test_metadata.db"

    # Patch DATABASE_PATH inside metadata module
    monkeypatch.setattr(
        "app.database.metadata.DATABASE_PATH",
        str(db_file)
    )

    return db_file


def test_create_metadata_table_creates_table_and_default_row(temp_db):
    metadata.db_create_metadata_table()

    conn = sqlite3.connect(metadata.DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM metadata")
    count = cursor.fetchone()[0]

    assert count == 1

    conn.close()


def test_get_metadata_returns_default_empty_dict(temp_db):
    metadata.db_create_metadata_table()

    result = metadata.db_get_metadata()

    assert result == {}


def test_update_metadata_and_fetch(temp_db):
    metadata.db_create_metadata_table()

    data = {"theme": "dark", "version": 1}
    success = metadata.db_update_metadata(data)

    assert success is True

    result = metadata.db_get_metadata()
    assert result == data


def test_update_metadata_with_existing_cursor(temp_db):
    metadata.db_create_metadata_table()

    conn = sqlite3.connect(metadata.DATABASE_PATH)
    cursor = conn.cursor()

    data = {"language": "en"}
    success = metadata.db_update_metadata(data, cursor=cursor)

    conn.commit()
    conn.close()

    assert success is True

    result = metadata.db_get_metadata()
    assert result == data


def test_get_metadata_returns_none_for_invalid_json(temp_db):
    metadata.db_create_metadata_table()

    conn = sqlite3.connect(metadata.DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM metadata")
    cursor.execute("INSERT INTO metadata (metadata) VALUES (?)", ("invalid_json",))

    conn.commit()
    conn.close()

    result = metadata.db_get_metadata()

    assert result is None