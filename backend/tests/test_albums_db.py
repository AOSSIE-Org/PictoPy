import os
import sqlite3
import tempfile
from typing import Iterator, List, Optional
from unittest.mock import MagicMock, patch

import bcrypt
import pytest

from app.database.albums import (
    db_create_albums_table,
    db_create_album_images_table,
    db_create_album_with_images,
    db_get_all_albums,
    db_get_album_by_name,
    db_get_album,
    db_insert_album,
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_add_images_to_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    db_get_album_cover_path,
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
    locked: bool = False,
    password: Optional[str] = None,
) -> str:
    """Insert an album and return its id."""
    db_insert_album(album_id, name, description, locked, password)
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


def make_images(db_path: str, image_ids: List[str]) -> None:
    """Seed real image rows so cover lookups have something to join against."""
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO images (id, path) VALUES (?, ?)",
        [(image_id, f"/photos/{image_id}.jpg") for image_id in image_ids],
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

    def test_migrates_a_legacy_is_hidden_schema(self, test_db):
        """Databases predating the rename must gain is_locked/cover_image_path.

        CREATE IF NOT EXISTS is a no-op on an existing table, so without the
        guarded ALTERs every shipped database 500s on the first album read.
        """
        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE albums")
        conn.execute(
            """
            CREATE TABLE albums (
                album_id TEXT PRIMARY KEY,
                album_name TEXT UNIQUE,
                description TEXT,
                is_hidden BOOLEAN DEFAULT 0,
                password_hash TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO albums (album_id, album_name, is_hidden) VALUES (?, ?, ?)",
            ("legacy-1", "Old", 1),
        )
        conn.commit()
        conn.close()

        db_create_albums_table()

        conn = sqlite3.connect(test_db)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(albums)")]
        conn.close()
        assert "is_hidden" not in columns
        assert {"is_locked", "cover_image_path"} <= set(columns)
        # the legacy row survives, its flag carried over under the new name
        legacy = db_get_all_albums()
        assert [
            (row["album_name"], row["description"], row["is_locked"]) for row in legacy
        ] == [("Old", None, True)]

    @pytest.mark.parametrize(
        "create_table", [db_create_albums_table, db_create_album_images_table]
    )
    def test_closes_the_connection_when_create_fails(self, create_table):
        """The finally-based cleanup must still run when the CREATE raises.

        Mocked deliberately: a real CREATE can't be made to fail while leaving
        the connection observable.
        """
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            conn = MagicMock()
            conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
            mock_connect.return_value = conn

            with pytest.raises(sqlite3.Error):
                create_table()

            conn.close.assert_called_once()


# ##############################
# Album CRUD
# ##############################


class TestAlbumCrud:
    def test_insert_then_fetch_by_id_and_name(self, test_db):
        make_album("album-1", "Summer Trip", "Fun times")

        by_id = db_get_album("album-1")
        assert by_id["album_id"] == "album-1"
        assert by_id["album_name"] == "Summer Trip"
        assert by_id["description"] == "Fun times"
        assert db_get_album_by_name("Summer Trip") == by_id

    def test_missing_album_returns_none(self, test_db):
        assert db_get_album("nope") is None
        assert db_get_album_by_name("nope") is None

    def test_duplicate_album_name_is_rejected(self, test_db):
        make_album("album-1", "Trip")
        # album_name carries a UNIQUE constraint
        with pytest.raises(sqlite3.IntegrityError):
            make_album("album-2", "Trip")

    def test_get_all_albums_returns_locked_albums_too(self, test_db):
        """Locked albums stay listed -- the password gates opening, not listing."""
        make_album("album-1", "Public")
        make_album("album-2", "Secret", locked=True, password="pw")

        rows = db_get_all_albums()
        assert sorted(row["album_name"] for row in rows) == ["Public", "Secret"]
        assert {row["album_name"]: row["is_locked"] for row in rows} == {
            "Public": False,
            "Secret": True,
        }

    def test_update_changes_fields(self, test_db):
        make_album("album-1", "Old", "Old desc")

        db_update_album("album-1", "New", "New desc", True, None)

        album = db_get_album("album-1")
        assert album["album_name"] == "New"
        assert album["description"] == "New desc"
        assert album["is_locked"] is True

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


class TestAlbumCreatedAt:
    def test_insert_stamps_a_creation_time(self, test_db):
        make_album("album-1", "Trip")

        assert db_get_album("album-1")["created_at"] is not None

    def test_create_with_images_stamps_a_creation_time(self, test_db):
        make_images(test_db, ["img-1"])

        db_create_album_with_images("album-1", "Paris", "", ["img-1"])

        assert db_get_album("album-1")["created_at"] is not None

    def test_edits_never_change_it(self, test_db):
        """Renaming, re-describing or adding photos is not a new creation."""
        make_album("album-1", "Trip")
        make_images(test_db, ["img-1"])
        created = db_get_album("album-1")["created_at"]

        db_update_album("album-1", "Trip Renamed", "A new description", False)
        db_add_images_to_album("album-1", ["img-1"])

        album = db_get_album("album-1")
        assert album["created_at"] == created
        # ...but all of that does count as an update.
        assert album["updated_at"] >= created

    def test_listing_keeps_insertion_order(self, test_db):
        """Albums predating created_at sort by when they were made."""
        make_album("album-1", "First")
        make_album("album-2", "Second")

        assert [album["album_id"] for album in db_get_all_albums()] == [
            "album-1",
            "album-2",
        ]

    def test_migration_adds_the_column_to_a_legacy_table(self, test_db):
        """A database shipped before created_at existed still upgrades."""
        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE albums")
        conn.execute(
            """
            CREATE TABLE albums (
                album_id TEXT PRIMARY KEY,
                album_name TEXT UNIQUE,
                description TEXT,
                is_hidden BOOLEAN DEFAULT 0,
                password_hash TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO albums (album_id, album_name) VALUES ('old-1', 'Old')"
        )
        conn.commit()
        conn.close()

        db_create_albums_table()

        old = db_get_album("old-1")
        assert old["album_name"] == "Old"
        # Nothing to backfill it with, so it reads as oldest.
        assert old["created_at"] is None
        # And the table still takes new albums.
        make_album("album-1", "New")
        assert db_get_album("album-1")["created_at"] is not None


class TestAlbumUpdatedAt:
    """
    updated_at is compared against a pinned earlier value rather than against
    a timestamp taken during the test: CURRENT_TIMESTAMP has one-second
    resolution, so two writes in the same second read as equal.
    """

    EARLIER = "2020-01-01 00:00:00"

    def set_updated_at(self, db_path: str, album_id: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE albums SET updated_at = ? WHERE album_id = ?",
            (self.EARLIER, album_id),
        )
        conn.commit()
        conn.close()

    def test_insert_stamps_an_update_time(self, test_db):
        make_album("album-1", "Trip")

        assert db_get_album("album-1")["updated_at"] is not None

    def test_editing_the_album_touches_it(self, test_db):
        make_album("album-1", "Trip")
        self.set_updated_at(test_db, "album-1")

        db_update_album("album-1", "Trip Renamed", "", False)

        assert db_get_album("album-1")["updated_at"] > self.EARLIER

    def test_adding_images_touches_it(self, test_db):
        """Adding photos is the commonest way an album changes."""
        make_album("album-1", "Trip")
        make_images(test_db, ["img-1"])
        self.set_updated_at(test_db, "album-1")

        db_add_images_to_album("album-1", ["img-1"])

        assert db_get_album("album-1")["updated_at"] > self.EARLIER

    def test_removing_an_image_touches_it(self, test_db):
        make_album("album-1", "Trip")
        make_images(test_db, ["img-1"])
        db_add_images_to_album("album-1", ["img-1"])
        self.set_updated_at(test_db, "album-1")

        db_remove_image_from_album("album-1", "img-1")

        assert db_get_album("album-1")["updated_at"] > self.EARLIER

    def test_removing_images_in_bulk_touches_it(self, test_db):
        make_album("album-1", "Trip")
        make_images(test_db, ["img-1", "img-2"])
        db_add_images_to_album("album-1", ["img-1", "img-2"])
        self.set_updated_at(test_db, "album-1")

        db_remove_images_from_album("album-1", ["img-1"])

        assert db_get_album("album-1")["updated_at"] > self.EARLIER

    def test_re_adding_the_same_images_leaves_it_alone(self, test_db):
        """Nothing was inserted, so nothing about the album changed."""
        make_album("album-1", "Trip")
        make_images(test_db, ["img-1"])
        db_add_images_to_album("album-1", ["img-1"])
        self.set_updated_at(test_db, "album-1")

        db_add_images_to_album("album-1", ["img-1"])

        assert db_get_album("album-1")["updated_at"] == self.EARLIER

    def test_bulk_removing_absent_images_leaves_it_alone(self, test_db):
        make_album("album-1", "Trip")
        self.set_updated_at(test_db, "album-1")

        db_remove_images_from_album("album-1", ["img-missing"])

        assert db_get_album("album-1")["updated_at"] == self.EARLIER

    def test_a_failed_removal_leaves_it_alone(self, test_db):
        """The image was never in the album, so nothing about it changed."""
        make_album("album-1", "Trip")
        self.set_updated_at(test_db, "album-1")

        with pytest.raises(ValueError):
            db_remove_image_from_album("album-1", "img-missing")

        assert db_get_album("album-1")["updated_at"] == self.EARLIER


class TestCreateAlbumWithImages:
    def test_creates_the_album_and_links_every_image(self, test_db):
        make_images(test_db, ["img-1", "img-2"])

        linked = db_create_album_with_images(
            "album-1", "Paris 2022", "July 2022", ["img-1", "img-2"]
        )

        assert linked == 2
        assert db_get_album_images("album-1") == ["img-1", "img-2"]
        album = db_get_album("album-1")
        assert album["album_name"] == "Paris 2022"
        assert album["description"] == "July 2022"
        # Always an open album: locking is done afterwards, from Edit Album.
        assert album["is_locked"] is False
        assert album["password_hash"] is None

    def test_an_unknown_image_leaves_no_album_behind(self, test_db):
        """The album and its links commit together, or not at all."""
        make_images(test_db, ["img-1"])

        with pytest.raises(sqlite3.IntegrityError):
            db_create_album_with_images(
                "album-1", "Paris 2022", "", ["img-1", "img-missing"]
            )

        assert db_get_album("album-1") is None

    def test_a_duplicate_name_is_rejected(self, test_db):
        make_album("album-1", "Paris 2022")
        make_images(test_db, ["img-1"])

        with pytest.raises(sqlite3.IntegrityError):
            db_create_album_with_images("album-2", "Paris 2022", "", ["img-1"])

        assert db_get_album("album-2") is None


# ##############################
# Password handling
# ##############################


class TestAlbumPassword:
    def test_password_is_stored_hashed(self, test_db):
        make_album("album-1", "Secret", locked=True, password="securepass")

        hashed = stored_hash(test_db, "album-1")
        assert hashed is not None
        assert hashed != "securepass"
        assert bcrypt.checkpw(b"securepass", hashed.encode())

    def test_verify_accepts_correct_and_rejects_wrong(self, test_db):
        make_album("album-1", "Secret", locked=True, password="securepass")

        assert verify_album_password("album-1", "securepass") is True
        assert verify_album_password("album-1", "wrongpass") is False

    def test_verify_returns_false_without_a_password(self, test_db):
        make_album("album-1", "Open")
        assert verify_album_password("album-1", "anything") is False

    def test_verify_returns_false_for_missing_album(self, test_db):
        assert verify_album_password("nope", "anything") is False

    def test_update_replaces_the_password(self, test_db):
        make_album("album-1", "Secret", locked=True, password="oldpass")

        db_update_album("album-1", "Secret", "", True, "newpass")

        assert verify_album_password("album-1", "newpass") is True
        assert verify_album_password("album-1", "oldpass") is False

    def test_update_without_password_keeps_the_existing_one(self, test_db):
        make_album("album-1", "Secret", locked=True, password="oldpass")
        before = stored_hash(test_db, "album-1")

        db_update_album("album-1", "Renamed", "", True, None)

        assert stored_hash(test_db, "album-1") == before
        assert verify_album_password("album-1", "oldpass") is True


# ##############################
# Cover image
# ##############################


class TestAlbumCoverPath:
    def test_uses_the_first_image_added(self, test_db):
        make_album("album-1")
        make_images(test_db, ["img-a", "img-b", "img-c"])
        link_images(test_db, "album-1", ["img-b", "img-a", "img-c"])

        assert db_get_album_cover_path("album-1") == "/photos/img-b.jpg"

    def test_returns_none_for_an_empty_album(self, test_db):
        make_album("album-1")

        assert db_get_album_cover_path("album-1") is None

    def test_returns_none_for_a_missing_album(self, test_db):
        assert db_get_album_cover_path("nope") is None

    def test_follows_the_album_when_the_first_image_is_removed(self, test_db):
        make_album("album-1")
        make_images(test_db, ["img-a", "img-b"])
        link_images(test_db, "album-1", ["img-a", "img-b"])

        db_remove_images_from_album("album-1", ["img-a"])

        assert db_get_album_cover_path("album-1") == "/photos/img-b.jpg"

    def test_ignores_images_in_other_albums(self, test_db):
        make_album("album-1")
        make_album("album-2", name="Other")
        make_images(test_db, ["img-a", "img-b"])
        link_images(test_db, "album-1", ["img-a"])
        link_images(test_db, "album-2", ["img-b"])

        assert db_get_album_cover_path("album-2") == "/photos/img-b.jpg"
