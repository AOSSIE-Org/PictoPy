import os
import sqlite3
import tempfile
from datetime import datetime
from typing import Any, Dict, Iterator

import pytest

from app.database.images import (
    db_create_images_table,
    db_bulk_insert_images,
    db_get_all_images,
    db_get_untagged_images,
    db_get_unembedded_images,
    db_update_image_tagged_status,
    db_insert_image_classes_batch,
    db_get_images_by_folder_ids,
    db_delete_images_by_ids,
    db_toggle_image_favourite_status,
    db_get_image_by_id,
    db_search_images_by_tag,
    db_get_images_by_ids,
    db_get_images_by_date_range,
    db_get_images_near_location,
    db_get_images_by_year_month,
    db_get_images_with_location,
    db_get_all_images_for_memories,
    db_mark_images_embedded,
)
from app.database.folders import db_create_folders_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.semantic_labels import db_create_semantic_labels_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the image/folder/mapping DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    # Build the production schema the image queries depend on. Order matters:
    # image_classes_display is a view over the image_classes table.
    db_create_YOLO_classes_table()  # mappings (tag names)
    db_create_folders_table()  # folders (FK target + AI_Tagging joins)
    db_create_images_table()  # images + image_classes
    db_create_semantic_labels_table()  # image_classes_display view

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def folder(test_db: str) -> str:
    """Insert a folder row (AI_Tagging on) to satisfy the images.folder_id FK."""
    folder_id = "folder-1"
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, AI_Tagging) "
        "VALUES (?, ?, 0, 1)",
        (folder_id, "/photos"),
    )
    conn.commit()
    conn.close()
    return folder_id


def make_image_record(
    image_id: str, path: str, folder_id: str, **overrides: Any
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "id": image_id,
        "path": path,
        "folder_id": folder_id,
        "thumbnailPath": f"/thumbs/thumbnail_{image_id}.jpg",
        "metadata": "{}",
        "isTagged": False,
        "isEmbedded": False,
        "latitude": None,
        "longitude": None,
        "captured_at": None,
    }
    record.update(overrides)
    return record


def add_tag(db_path: str, image_id: str, class_id: int, name: str) -> None:
    """Register a mapping name and attach it to an image via image_classes."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)",
        (class_id, name),
    )
    conn.execute(
        "INSERT OR IGNORE INTO image_classes (image_id, class_id) VALUES (?, ?)",
        (image_id, class_id),
    )
    conn.commit()
    conn.close()


def drop_object(db_path: str, kind: str, name: str) -> None:
    """Drop a table/view so the next query against it raises sqlite3.Error."""
    conn = sqlite3.connect(db_path)
    conn.execute(f"DROP {kind} IF EXISTS {name}")
    conn.commit()
    conn.close()


# ##############################
# Table creation
# ##############################


class TestCreateImagesTable:
    def test_creates_images_and_image_classes_tables(self, test_db):
        conn = sqlite3.connect(test_db)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "images" in tables
        assert "image_classes" in tables

    def test_is_idempotent(self, test_db):
        # Calling create again on an existing schema must not raise
        db_create_images_table()

    def test_adds_score_column_to_legacy_image_classes(self, test_db):
        # A pre-score image_classes table must gain the column via the guarded ALTER
        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE image_classes")
        conn.execute(
            "CREATE TABLE image_classes (image_id TEXT, class_id INTEGER, "
            "PRIMARY KEY (image_id, class_id))"
        )
        conn.commit()
        conn.close()

        db_create_images_table()

        conn = sqlite3.connect(test_db)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(image_classes)")}
        conn.close()
        assert "score" in columns


# ##############################
# Bulk insert
# ##############################


class TestBulkInsertImages:
    def test_empty_list_is_a_noop_success(self, test_db):
        assert db_bulk_insert_images([]) is True

    def test_inserts_records(self, folder, test_db):
        records = [
            make_image_record("img-1", "/photos/a.jpg", folder),
            make_image_record("img-2", "/photos/b.jpg", folder),
        ]
        assert db_bulk_insert_images(records) is True
        assert len(db_get_all_images()) == 2

    def test_conflict_on_path_upserts(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        # Same path, now tagged -> row is updated in place, not duplicated
        db_bulk_insert_images(
            [make_image_record("img-1", "/photos/a.jpg", folder, isTagged=True)]
        )
        images = db_get_all_images()
        assert len(images) == 1
        assert images[0]["isTagged"] is True

    def test_foreign_key_violation_returns_false(self, test_db):
        # folder_id has no matching folders row -> FK failure -> rollback
        record = make_image_record("img-1", "/photos/a.jpg", "missing-folder")
        assert db_bulk_insert_images([record]) is False
        assert db_get_all_images() == []


# ##############################
# Reading images
# ##############################


class TestGetAllImages:
    def test_returns_empty_when_no_images(self, test_db):
        assert db_get_all_images() == []

    def test_returns_tags_and_none_when_untagged(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder),
                make_image_record("img-2", "/photos/b.jpg", folder),
            ]
        )
        add_tag(test_db, "img-1", 9001, "sunset")

        by_id = {img["id"]: img for img in db_get_all_images()}
        assert by_id["img-1"]["tags"] == ["sunset"]
        assert by_id["img-2"]["tags"] is None

    def test_tagged_filter(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder, isTagged=True),
                make_image_record("img-2", "/photos/b.jpg", folder, isTagged=False),
            ]
        )
        tagged = db_get_all_images(tagged=True)
        assert [img["id"] for img in tagged] == ["img-1"]


class TestGetImageById:
    def test_returns_none_when_missing(self, test_db):
        assert db_get_image_by_id("nope") is None

    def test_parses_metadata(self, folder, test_db):
        db_bulk_insert_images(
            [make_image_record("img-1", "/photos/a.jpg", folder, metadata='{"k": 1}')]
        )
        image = db_get_image_by_id("img-1")
        assert image["metadata"] == {"k": 1}
        assert image["isFavourite"] is False

    def test_invalid_metadata_falls_back_to_empty(self, folder, test_db):
        db_bulk_insert_images(
            [make_image_record("img-1", "/photos/a.jpg", folder, metadata="not json")]
        )
        assert db_get_image_by_id("img-1")["metadata"] == {}


class TestUntaggedAndUnembedded:
    def test_untagged_lists_only_untagged_in_ai_folders(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder, isTagged=False),
                make_image_record("img-2", "/photos/b.jpg", folder, isTagged=True),
            ]
        )
        assert [img["id"] for img in db_get_untagged_images()] == ["img-1"]

    def test_unembedded_lists_only_unembedded_in_ai_folders(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder, isEmbedded=False),
                make_image_record("img-2", "/photos/b.jpg", folder, isEmbedded=True),
            ]
        )
        assert [img["id"] for img in db_get_unembedded_images()] == ["img-1"]


# ##############################
# Tagging, classes and status
# ##############################


class TestTaggedStatusAndClasses:
    def test_update_tagged_status(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        assert db_update_image_tagged_status("img-1", True) is True
        assert db_get_image_by_id("img-1")["isTagged"] is True

    def test_update_tagged_status_missing_image(self, test_db):
        assert db_update_image_tagged_status("nope", True) is False

    def test_insert_image_classes_batch_empty(self, test_db):
        assert db_insert_image_classes_batch([]) is True

    def test_insert_image_classes_batch_ignores_duplicates(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        assert db_insert_image_classes_batch([("img-1", 0), ("img-1", 0)]) is True

        conn = sqlite3.connect(test_db)
        count = conn.execute(
            "SELECT COUNT(*) FROM image_classes WHERE image_id = 'img-1'"
        ).fetchone()[0]
        conn.close()
        assert count == 1


class TestFavouriteStatus:
    def test_toggles_on_then_off(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        assert db_toggle_image_favourite_status("img-1") is True
        assert db_get_image_by_id("img-1")["isFavourite"] is True
        assert db_toggle_image_favourite_status("img-1") is True
        assert db_get_image_by_id("img-1")["isFavourite"] is False

    def test_missing_image_returns_false(self, test_db):
        assert db_toggle_image_favourite_status("nope") is False


# ##############################
# Folder queries and deletion
# ##############################


class TestFolderQueriesAndDeletion:
    def test_get_images_by_folder_ids_empty(self, test_db):
        assert db_get_images_by_folder_ids([]) == []

    def test_get_images_by_folder_ids(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder),
                make_image_record("img-2", "/photos/b.jpg", folder),
            ]
        )
        rows = db_get_images_by_folder_ids([folder])
        assert {row[0] for row in rows} == {"img-1", "img-2"}
        assert rows[0][1].startswith("/photos/")

    def test_delete_by_ids_empty(self, test_db):
        assert db_delete_images_by_ids([]) is True

    def test_delete_by_ids_cascades_to_image_classes(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder),
                make_image_record("img-2", "/photos/b.jpg", folder),
            ]
        )
        db_insert_image_classes_batch([("img-1", 0)])

        # The junction row must exist first, or the cascade assertion is vacuous
        conn = sqlite3.connect(test_db)
        before = conn.execute(
            "SELECT COUNT(*) FROM image_classes WHERE image_id = 'img-1'"
        ).fetchone()[0]
        conn.close()
        assert before == 1

        assert db_delete_images_by_ids(["img-1"]) is True
        assert [img["id"] for img in db_get_all_images()] == ["img-2"]

        conn = sqlite3.connect(test_db)
        remaining = conn.execute(
            "SELECT COUNT(*) FROM image_classes WHERE image_id = 'img-1'"
        ).fetchone()[0]
        conn.close()
        assert remaining == 0


# ##############################
# Search and lookup by ids
# ##############################


class TestSearchAndGetByIds:
    def test_search_by_tag_is_case_insensitive(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        add_tag(test_db, "img-1", 9001, "sunset")

        results = db_search_images_by_tag("SUNSET")
        assert [img["id"] for img in results] == ["img-1"]
        assert results[0]["tags"] == ["sunset"]

    def test_search_by_tag_no_match(self, folder, test_db):
        db_bulk_insert_images([make_image_record("img-1", "/photos/a.jpg", folder)])
        assert db_search_images_by_tag("nothing") == []

    def test_get_images_by_ids_empty(self, test_db):
        assert db_get_images_by_ids([]) == []

    def test_get_images_by_ids_preserves_request_order(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder),
                make_image_record("img-2", "/photos/b.jpg", folder),
                make_image_record("img-3", "/photos/c.jpg", folder),
            ]
        )
        # Request out of insertion order, with one id that does not exist
        results = db_get_images_by_ids(["img-3", "img-1", "missing"])
        assert [img["id"] for img in results] == ["img-3", "img-1"]


# ##############################
# Memories: location and time
# ##############################


class TestMemoriesQueries:
    def _seed_memory_images(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record(
                    "img-near",
                    "/photos/near.jpg",
                    folder,
                    latitude=40.001,
                    longitude=-74.001,
                    captured_at="2024-06-15 12:00:00",
                ),
                make_image_record(
                    "img-far",
                    "/photos/far.jpg",
                    folder,
                    latitude=41.0,
                    longitude=-75.0,
                    captured_at="2024-07-15 12:00:00",
                ),
                make_image_record(
                    "img-nogps",
                    "/photos/nogps.jpg",
                    folder,
                    captured_at="2024-06-20 09:00:00",
                ),
            ]
        )

    def test_by_date_range(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        results = db_get_images_by_date_range(
            datetime(2024, 6, 1), datetime(2024, 6, 30)
        )
        assert {img["id"] for img in results} == {"img-near", "img-nogps"}

    def test_by_date_range_favorites_only(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        db_toggle_image_favourite_status("img-near")
        results = db_get_images_by_date_range(
            datetime(2024, 6, 1), datetime(2024, 6, 30), include_favorites_only=True
        )
        assert [img["id"] for img in results] == ["img-near"]

    def test_near_location_excludes_far_and_null(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        results = db_get_images_near_location(40.0, -74.0, radius_km=5.0)
        assert [img["id"] for img in results] == ["img-near"]

    def test_by_year_month(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        results = db_get_images_by_year_month(2024, 6)
        assert {img["id"] for img in results} == {"img-near", "img-nogps"}

    def test_with_location_only_returns_geotagged(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        results = db_get_images_with_location()
        assert {img["id"] for img in results} == {"img-near", "img-far"}

    def test_all_for_memories_returns_everything(self, folder, test_db):
        self._seed_memory_images(folder, test_db)
        results = db_get_all_images_for_memories()
        assert {img["id"] for img in results} == {"img-near", "img-far", "img-nogps"}


# ##############################
# Marking embedded
# ##############################


class TestMarkImagesEmbedded:
    def test_empty_list_is_a_noop_success(self, test_db):
        assert db_mark_images_embedded([]) is True

    def test_marks_images_embedded(self, folder, test_db):
        db_bulk_insert_images(
            [
                make_image_record("img-1", "/photos/a.jpg", folder, isEmbedded=False),
                make_image_record("img-2", "/photos/b.jpg", folder, isEmbedded=False),
            ]
        )
        assert db_mark_images_embedded(["img-1", "img-2"]) is True
        assert db_get_unembedded_images() == []


# ##############################
# Error handling
# ##############################


class TestErrorHandling:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: db_get_all_images(),
            lambda: db_get_images_by_date_range(
                datetime(2024, 1, 1), datetime(2024, 12, 31)
            ),
            lambda: db_get_images_near_location(0.0, 0.0),
            lambda: db_get_images_by_year_month(2024, 1),
            lambda: db_get_images_with_location(),
            lambda: db_get_all_images_for_memories(),
        ],
    )
    def test_view_read_errors_return_empty(self, test_db, call):
        # These queries join image_classes_display; without it they must not crash
        drop_object(test_db, "VIEW", "image_classes_display")
        assert call() == []

    def test_search_by_tag_reraises_on_db_error(self, test_db):
        drop_object(test_db, "VIEW", "image_classes_display")
        with pytest.raises(sqlite3.Error):
            db_search_images_by_tag("x")

    def test_get_images_by_ids_reraises_on_db_error(self, test_db):
        drop_object(test_db, "VIEW", "image_classes_display")
        with pytest.raises(sqlite3.Error):
            db_get_images_by_ids(["x"])

    def test_get_by_folder_ids_returns_empty_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "images")
        assert db_get_images_by_folder_ids([1]) == []

    def test_update_tagged_status_returns_false_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "images")
        assert db_update_image_tagged_status("x", True) is False

    def test_delete_by_ids_returns_false_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "images")
        assert db_delete_images_by_ids(["x"]) is False

    def test_toggle_favourite_returns_false_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "images")
        assert db_toggle_image_favourite_status("x") is False

    def test_mark_embedded_returns_false_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "images")
        assert db_mark_images_embedded(["x"]) is False

    def test_insert_image_classes_returns_false_on_db_error(self, test_db):
        drop_object(test_db, "TABLE", "image_classes")
        assert db_insert_image_classes_batch([("x", 0)]) is False
