"""
Deleting a photo from inside PictoPy. Two outcomes the user picks between:
remove it from the gallery only, or delete the file from its folder as well.
The gallery-only case has to survive the watcher's next sync-folder, which is
what the exclusion table is for.
"""

import os
import sqlite3
import tempfile
from typing import Iterator, List

import pytest
from PIL import Image

from app.database.folders import db_create_folders_table
from app.database.images import (
    db_create_images_table,
    db_get_excluded_image_paths,
)
from app.database.semantic_labels import db_create_semantic_labels_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.utils.images import (
    image_util_delete_images,
    image_util_process_folder_images,
    image_util_remove_files,
)

FOLDER_ID = "folder-1"


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the image/folder DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    db_create_YOLO_classes_table()  # mappings (image_classes FK target)
    db_create_folders_table()  # folders (images.folder_id FK target)
    db_create_images_table()
    db_create_semantic_labels_table()  # image_classes_display view

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def library(tmp_path, test_db, monkeypatch) -> Iterator[str]:
    """A folder of real JPEGs, scanned into the database like the app would."""
    photos = tmp_path / "photos"
    photos.mkdir()
    thumbs = tmp_path / "thumbs"
    thumbs.mkdir()
    monkeypatch.setattr("app.utils.images.THUMBNAIL_IMAGES_PATH", str(thumbs))

    for index in range(3):
        Image.new("RGB", (8, 8), (index * 20, 40, 90)).save(
            photos / f"p{index}.jpg", "JPEG"
        )

    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
        "AI_Tagging) VALUES (?, ?, 0, 1)",
        (FOLDER_ID, str(photos)),
    )
    conn.commit()
    conn.close()

    image_util_process_folder_images([(str(photos), FOLDER_ID, False)])
    yield str(photos)


def _rows(db_path: str) -> List[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, path, thumbnailPath FROM images").fetchall()
    conn.close()
    return rows


def _first(db_path: str) -> tuple:
    """(id, path, thumbnailPath) of one image already in the gallery."""
    return _rows(db_path)[0]


class TestRemoveFiles:
    def test_a_file_is_deleted(self, tmp_path):
        target = tmp_path / "a.jpg"
        target.write_bytes(b"x")
        assert image_util_remove_files([str(target)]) == []
        assert not target.exists()

    def test_a_file_already_gone_is_not_a_failure(self, tmp_path):
        """Thumbnails go missing on their own; the outcome we wanted is the same."""
        assert image_util_remove_files([str(tmp_path / "gone.jpg")]) == []

    def test_empty_and_none_paths_are_skipped(self):
        assert image_util_remove_files([None, ""]) == []

    def test_a_directory_is_reported_rather_than_raising(self, tmp_path):
        """os.remove on a directory raises OSError, which callers must survive."""
        assert image_util_remove_files([str(tmp_path)]) == [str(tmp_path)]


class TestGalleryOnlyDelete:
    def test_the_row_goes_but_the_file_stays(self, library, test_db):
        image_id, path, _ = _first(test_db)

        result = image_util_delete_images([image_id])

        assert result["deleted_ids"] == [image_id]
        assert result["failed_paths"] == []
        assert os.path.exists(path)
        assert image_id not in [row[0] for row in _rows(test_db)]

    def test_the_thumbnail_goes_because_it_is_our_own_cache(self, library, test_db):
        image_id, _, thumbnail_path = _first(test_db)
        assert os.path.exists(thumbnail_path)

        image_util_delete_images([image_id])

        assert not os.path.exists(thumbnail_path)

    def test_the_path_is_recorded_as_excluded(self, library, test_db):
        image_id, path, _ = _first(test_db)

        image_util_delete_images([image_id])

        expected = os.path.normcase(os.path.abspath(path))
        assert expected in db_get_excluded_image_paths()

    def test_a_rescan_does_not_bring_it_back(self, library, test_db):
        """The regression the exclusion table exists to prevent."""
        image_id, path, _ = _first(test_db)
        image_util_delete_images([image_id])

        image_util_process_folder_images([(library, FOLDER_ID, False)])

        assert path not in [row[1] for row in _rows(test_db)]

    def test_the_other_photos_are_left_alone(self, library, test_db):
        image_id, _, _ = _first(test_db)

        image_util_delete_images([image_id])

        assert len(_rows(test_db)) == 2

    def test_removing_the_folder_clears_its_exclusions(self, library, test_db):
        """Re-adding the folder is the only way back, so the cascade has to work."""
        image_id, _, _ = _first(test_db)
        image_util_delete_images([image_id])

        conn = sqlite3.connect(test_db)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM folders WHERE folder_id = ?", (FOLDER_ID,))
        conn.commit()
        conn.close()

        assert db_get_excluded_image_paths() == set()


class TestDeleteFromDevice:
    def test_the_file_and_the_row_both_go(self, library, test_db):
        image_id, path, _ = _first(test_db)

        result = image_util_delete_images([image_id], delete_from_device=True)

        assert result["deleted_ids"] == [image_id]
        assert not os.path.exists(path)
        assert image_id not in [row[0] for row in _rows(test_db)]

    def test_no_exclusion_is_recorded(self, library, test_db):
        """The file is gone, so there is nothing for a later scan to skip."""
        image_id, _, _ = _first(test_db)

        image_util_delete_images([image_id], delete_from_device=True)

        assert db_get_excluded_image_paths() == set()

    def test_a_file_that_cannot_be_deleted_keeps_its_row(self, library, test_db):
        """Never claim a photo is gone while the file is still in the folder."""
        image_id, path, _ = _first(test_db)

        def refuse(file_paths):
            return [p for p in file_paths if p == path]

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr("app.utils.images.image_util_remove_files", refuse)
            result = image_util_delete_images([image_id], delete_from_device=True)

        assert result["deleted_ids"] == []
        assert result["failed_paths"] == [path]
        assert image_id in [row[0] for row in _rows(test_db)]


class TestUnknownIds:
    def test_an_unknown_id_deletes_nothing(self, library, test_db):
        result = image_util_delete_images(["not-a-real-id"])

        assert result == {"deleted_ids": [], "failed_paths": []}
        assert len(_rows(test_db)) == 3

    def test_an_empty_list_deletes_nothing(self, library, test_db):
        result = image_util_delete_images([])

        assert result == {"deleted_ids": [], "failed_paths": []}
        assert len(_rows(test_db)) == 3
