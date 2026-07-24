import os
import sqlite3
import tempfile
from typing import Iterator, List, Optional

import bcrypt
import pytest

from app.database.albums import (
    db_create_albums_table,
    db_create_album_images_table,
    db_get_all_albums,
    db_get_album_by_name,
    db_get_album,
    db_insert_album,
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_remove_images_from_album,
    verify_album_password,
)
from app.database.images import db_create_images_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the album DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.albums.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    # db_delete_album goes through the shared get_db_connection helper
    monkeypatch.setattr("app.database.connection.DATABASE_PATH", db_path)

    db_create_albums_table()
    db_create_album_images_table()
    # album_images FKs into images, and get_db_connection enforces foreign
    # keys -- deleting an album can't resolve the cascade without this table.
    db_create_images_table()

    yield db_path

    os.unlink(db_path)


def make_album(
    album_id: str = "album-1",
    name: str = "Trip",
    description: str = "",
    hidden: bool = False,
    password: Optional[str] = None,
) -> str:
    """Insert an album and return its id."""
    db_insert_album(album_id, name, description, hidden, password)
    return album_id


def link_images(db_path: str, album_id: str, image_ids: List[str]) -> None:
    """Seed album_images rows directly -- these reads don't need real images."""
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO album_images (album_id, image_id) VALUES (?, ?)",
        [(album_id, image_id) for image_id in image_ids],
    )
    conn.commit()
    conn.close()


def stored_hash(db_path: str, album_id: str) -> Optional[str]:
    """Read an album's raw password_hash straight from the table."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT password_hash FROM albums WHERE album_id = ?", (album_id,)
    ).fetchone()
    conn.close()
    return row[0]


# ##############################
# Table creation
# ##############################


class TestAlbumTables:
    def test_creates_both_tables(self, test_db):
        conn = sqlite3.connect(test_db)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        conn.close()
        assert {"albums", "album_images"} <= tables

    def test_is_idempotent(self, test_db):
        # Re-running against an existing schema must not raise
        db_create_albums_table()
        db_create_album_images_table()


# ##############################
# Album CRUD
# ##############################


class TestAlbumCrud:
    def test_insert_then_fetch_by_id_and_name(self, test_db):
        make_album("album-1", "Summer Trip", "Fun times")

        by_id = db_get_album("album-1")
        assert by_id[:3] == ("album-1", "Summer Trip", "Fun times")
        assert db_get_album_by_name("Summer Trip") == by_id

    def test_missing_album_returns_none(self, test_db):
        assert db_get_album("nope") is None
        assert db_get_album_by_name("nope") is None

    def test_duplicate_album_name_is_rejected(self, test_db):
        make_album("album-1", "Trip")
        # album_name carries a UNIQUE constraint
        with pytest.raises(sqlite3.IntegrityError):
            make_album("album-2", "Trip")

    def test_get_all_albums_hides_hidden_by_default(self, test_db):
        make_album("album-1", "Public")
        make_album("album-2", "Secret", hidden=True, password="pw")

        visible = [row[1] for row in db_get_all_albums(show_hidden=False)]
        every = [row[1] for row in db_get_all_albums(show_hidden=True)]
        assert visible == ["Public"]
        assert sorted(every) == ["Public", "Secret"]

    def test_update_changes_fields(self, test_db):
        make_album("album-1", "Old", "Old desc")

        db_update_album("album-1", "New", "New desc", True, None)

        album = db_get_album("album-1")
        assert album[1] == "New"
        assert album[2] == "New desc"
        assert album[3] == 1

    def test_delete_removes_the_row(self, test_db):
        make_album("album-1", "Trip")
        db_delete_album("album-1")
        assert db_get_album("album-1") is None


# ##############################
# Album images
# ##############################


class TestAlbumImages:
    def test_returns_linked_image_ids(self, test_db):
        make_album("album-1", "Trip")
        link_images(test_db, "album-1", ["img-1", "img-2", "img-3"])

        assert db_get_album_images("album-1") == ["img-1", "img-2", "img-3"]

    def test_returns_empty_for_album_without_images(self, test_db):
        make_album("album-1", "Trip")
        assert db_get_album_images("album-1") == []

    def test_remove_images_drops_only_the_named_ones(self, test_db):
        make_album("album-1", "Trip")
        link_images(test_db, "album-1", ["img-1", "img-2", "img-3"])

        db_remove_images_from_album("album-1", ["img-1", "img-3"])

        assert db_get_album_images("album-1") == ["img-2"]


# ##############################
# Password handling
# ##############################


class TestAlbumPassword:
    def test_password_is_stored_hashed(self, test_db):
        make_album("album-1", "Secret", hidden=True, password="securepass")

        hashed = stored_hash(test_db, "album-1")
        assert hashed is not None
        assert hashed != "securepass"
        assert bcrypt.checkpw(b"securepass", hashed.encode())

    def test_verify_accepts_correct_and_rejects_wrong(self, test_db):
        make_album("album-1", "Secret", hidden=True, password="securepass")

        assert verify_album_password("album-1", "securepass") is True
        assert verify_album_password("album-1", "wrongpass") is False

    def test_verify_returns_false_without_a_password(self, test_db):
        make_album("album-1", "Open")
        assert verify_album_password("album-1", "anything") is False

    def test_verify_returns_false_for_missing_album(self, test_db):
        assert verify_album_password("nope", "anything") is False

    def test_update_replaces_the_password(self, test_db):
        make_album("album-1", "Secret", hidden=True, password="oldpass")

        db_update_album("album-1", "Secret", "", True, "newpass")

        assert verify_album_password("album-1", "newpass") is True
        assert verify_album_password("album-1", "oldpass") is False

    def test_update_without_password_keeps_the_existing_one(self, test_db):
        make_album("album-1", "Secret", hidden=True, password="oldpass")
        before = stored_hash(test_db, "album-1")

        db_update_album("album-1", "Renamed", "", True, None)

        assert stored_hash(test_db, "album-1") == before
        assert verify_album_password("album-1", "oldpass") is True
