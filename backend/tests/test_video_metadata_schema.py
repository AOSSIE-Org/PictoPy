import os
import sqlite3
from pathlib import Path

from app.database.images import db_create_images_table


def test_db_create_images_table_adds_video_columns(tmp_path, monkeypatch):
    """
    Ensure db_create_images_table adds is_video, duration, and codec columns
    to an existing images table that was created without them.
    """

    db_path = tmp_path / "test_video_schema.sqlite3"

    # Create an "old schema" images table without video columns
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE images (
                id TEXT PRIMARY KEY,
                path VARCHAR UNIQUE,
                folder_id INTEGER,
                thumbnailPath TEXT UNIQUE,
                metadata TEXT,
                isTagged BOOLEAN DEFAULT 0,
                isFavourite BOOLEAN DEFAULT 0,
                latitude REAL,
                longitude REAL,
                captured_at DATETIME
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    # Point the images module to this temporary database
    monkeypatch.setattr("app.database.images.DATABASE_PATH", str(db_path))

    # This should run CREATE TABLE IF NOT EXISTS (no-op on existing)
    # and then ensure the new video-related columns exist via ALTER TABLE.
    db_create_images_table()

    # Verify that the new columns are present
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("PRAGMA table_info(images)")
        columns = {row[1] for row in cursor.fetchall()}
    finally:
        conn.close()

    assert "is_video" in columns
    assert "duration" in columns
    assert "codec" in columns

