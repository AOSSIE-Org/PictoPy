import os
import sqlite3
import tempfile
import shutil
from unittest.mock import MagicMock

import cv2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database.videos import (
    db_create_videos_table,
    db_bulk_insert_videos,
    db_get_all_videos,
    db_get_videos_by_folder_ids,
    db_delete_videos_by_ids,
    db_toggle_video_favourite_status,
    db_get_video_by_id,
)
from app.utils.videos import (
    video_util_is_valid_video,
    video_util_get_videos_from_folder,
    video_util_generate_thumbnail,
    video_util_extract_metadata,
    video_util_prepare_video_records,
    video_util_process_folder_videos,
    video_util_collect_superseded_thumbnails,
    video_util_source_is_unchanged,
    video_util_remove_thumbnail_files,
)
from app.routes.videos import router as videos_router

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Point every video/folder DB module at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.videos.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)

    from app.database.folders import db_create_folders_table

    db_create_folders_table()
    db_create_videos_table()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def test_folder_id(test_db):
    """Insert a folder row to satisfy the videos.folder_id FK."""
    folder_id = "test-folder-1"
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time) VALUES (?, ?, 0)",
        (folder_id, os.path.abspath("test-folder-path")),
    )
    conn.commit()
    conn.close()
    return folder_id


@pytest.fixture
def temp_media_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def real_video_file(temp_media_dir):
    """Write a tiny real video via cv2.VideoWriter (MJPG/.avi is the portable combo)."""
    import numpy as np

    video_path = os.path.join(temp_media_dir, "sample.avi")
    writer = cv2.VideoWriter(
        video_path, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 64)
    )
    if not writer.isOpened():
        pytest.skip("cv2.VideoWriter unavailable in this environment")
    for i in range(10):
        frame = np.full((64, 64, 3), i * 20, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return video_path


@pytest.fixture
def client(test_db):
    app = FastAPI()
    app.include_router(videos_router, prefix="/videos")
    return TestClient(app)


def make_video_record(video_id, path, folder_id, **overrides):
    record = {
        "id": video_id,
        "path": path,
        "folder_id": folder_id,
        "thumbnailPath": f"/thumbs/thumbnail_{video_id}.jpg",
        "metadata": "{}",
        "isTagged": False,
        "captured_at": "2026-01-01T00:00:00",
    }
    record.update(overrides)
    return record


# ##############################
# Validation and scanning
# ##############################


class TestVideoValidation:
    def test_accepts_supported_extensions(self, temp_media_dir):
        for ext in (".mp4", ".mov", ".webm", ".m4v"):
            path = os.path.join(temp_media_dir, f"video{ext}")
            with open(path, "wb") as f:
                f.write(b"data")
            assert video_util_is_valid_video(path) is True

    def test_rejects_unsupported_extensions(self, temp_media_dir):
        for ext in (".mkv", ".avi", ".wmv", ".txt", ".jpg"):
            path = os.path.join(temp_media_dir, f"file{ext}")
            with open(path, "wb") as f:
                f.write(b"data")
            assert video_util_is_valid_video(path) is False

    def test_rejects_empty_file(self, temp_media_dir):
        path = os.path.join(temp_media_dir, "empty.mp4")
        open(path, "wb").close()
        assert video_util_is_valid_video(path) is False

    def test_rejects_missing_file(self, temp_media_dir):
        assert (
            video_util_is_valid_video(os.path.join(temp_media_dir, "nope.mp4")) is False
        )


class TestVideoScanning:
    def _touch(self, path, content=b"data"):
        with open(path, "wb") as f:
            f.write(content)

    def test_returns_only_videos_from_mixed_folder(self, temp_media_dir):
        self._touch(os.path.join(temp_media_dir, "a.mp4"))
        self._touch(os.path.join(temp_media_dir, "b.jpg"))
        self._touch(os.path.join(temp_media_dir, "c.webm"))
        self._touch(os.path.join(temp_media_dir, "d.mkv"))

        found = video_util_get_videos_from_folder(temp_media_dir)
        names = sorted(os.path.basename(p) for p in found)
        assert names == ["a.mp4", "c.webm"]

    def test_recursive_vs_non_recursive(self, temp_media_dir):
        sub = os.path.join(temp_media_dir, "sub")
        os.makedirs(sub)
        self._touch(os.path.join(temp_media_dir, "top.mp4"))
        self._touch(os.path.join(sub, "nested.mp4"))

        recursive = video_util_get_videos_from_folder(temp_media_dir, recursive=True)
        flat = video_util_get_videos_from_folder(temp_media_dir, recursive=False)
        assert len(recursive) == 2
        assert len(flat) == 1


# ##############################
# Thumbnails and metadata
# ##############################


class TestVideoThumbnailAndMetadata:
    def test_generate_thumbnail_from_real_video(self, real_video_file, temp_media_dir):
        thumb_path = os.path.join(temp_media_dir, "thumb.jpg")
        assert video_util_generate_thumbnail(real_video_file, thumb_path) is True
        assert os.path.exists(thumb_path)
        img = cv2.imread(thumb_path)
        assert img is not None

    def test_generate_thumbnail_fails_on_non_video(self, temp_media_dir):
        fake = os.path.join(temp_media_dir, "fake.mp4")
        with open(fake, "w") as f:
            f.write("not a video")
        thumb_path = os.path.join(temp_media_dir, "thumb.jpg")
        assert video_util_generate_thumbnail(fake, thumb_path) is False

    def test_extract_metadata_from_real_video(self, real_video_file):
        metadata = video_util_extract_metadata(real_video_file)
        assert metadata["name"] == "sample.avi"
        assert metadata["width"] == 64
        assert metadata["height"] == 64
        assert metadata["fps"] == pytest.approx(10.0)
        assert metadata["duration"] == pytest.approx(1.0)
        assert metadata["file_size"] > 0
        assert metadata["date_created"] is not None

    def test_extract_metadata_undecodable_file(self, temp_media_dir):
        fake = os.path.join(temp_media_dir, "fake.mp4")
        with open(fake, "w") as f:
            f.write("not a video")
        metadata = video_util_extract_metadata(fake)
        assert metadata["width"] == 0
        assert metadata["duration"] is None
        assert metadata["file_size"] > 0

    def test_prepare_records_keeps_undecodable_video(self, temp_media_dir, monkeypatch):
        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        os.makedirs(thumb_dir)
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        fake = os.path.join(temp_media_dir, "fake.mp4")
        with open(fake, "w") as f:
            f.write("not a video")

        records = video_util_prepare_video_records(
            [fake], {os.path.abspath(temp_media_dir): 1}
        )
        assert len(records) == 1
        assert records[0]["thumbnailPath"] is None
        assert records[0]["path"] == fake


class TestProcessFolderVideos:
    def test_scan_insert_and_obsolete_removal(
        self, test_db, test_folder_id, real_video_file, temp_media_dir, monkeypatch
    ):
        """End-to-end: scan a folder, insert records, then clean up removed files."""
        from app.utils.videos import video_util_process_folder_videos

        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        # Extension whitelist excludes .avi, so give the real video an .mp4 name
        video_path = os.path.join(temp_media_dir, "clip.mp4")
        shutil.copyfile(real_video_file, video_path)
        os.remove(real_video_file)

        folder_data = [(temp_media_dir, test_folder_id, False)]
        assert video_util_process_folder_videos(folder_data) is True

        videos = db_get_all_videos()
        assert len(videos) == 1
        assert videos[0]["path"] == video_path
        assert videos[0]["thumbnailPath"] is not None
        assert os.path.exists(videos[0]["thumbnailPath"])
        assert videos[0]["metadata"]["duration"] == pytest.approx(1.0)

        # Deleting the file makes the next pass remove the row and thumbnail
        thumbnail_path = videos[0]["thumbnailPath"]
        os.remove(video_path)
        assert video_util_process_folder_videos(folder_data) is True
        assert db_get_all_videos() == []
        assert not os.path.exists(thumbnail_path)

    def test_repeat_scan_reuses_existing_thumbnails(
        self, test_db, test_folder_id, real_video_file, temp_media_dir, monkeypatch
    ):
        """Re-scanning an unchanged folder must not orphan the previous thumbnail."""
        from app.utils.videos import video_util_process_folder_videos

        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        video_path = os.path.join(temp_media_dir, "clip.mp4")
        shutil.copyfile(real_video_file, video_path)
        os.remove(real_video_file)

        folder_data = [(temp_media_dir, test_folder_id, False)]
        assert video_util_process_folder_videos(folder_data) is True

        first = db_get_all_videos()
        assert len(os.listdir(thumb_dir)) == 1

        # A second pass over unchanged files should be a no-op
        assert video_util_process_folder_videos(folder_data) is True

        second = db_get_all_videos()
        assert len(second) == 1
        assert second[0]["id"] == first[0]["id"]
        assert second[0]["thumbnailPath"] == first[0]["thumbnailPath"]
        assert len(os.listdir(thumb_dir)) == 1

    def test_replacing_the_source_refreshes_the_record(
        self, test_db, test_folder_id, real_video_file, temp_media_dir, monkeypatch
    ):
        """A different video swapped in at the same path must not stay stale."""
        from app.utils.videos import video_util_process_folder_videos

        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        video_path = os.path.join(temp_media_dir, "clip.mp4")
        shutil.copyfile(real_video_file, video_path)

        folder_data = [(temp_media_dir, test_folder_id, False)]
        video_util_process_folder_videos(folder_data)
        first = db_get_all_videos()[0]

        # Swap in a longer, larger clip at the same path
        import numpy as np

        writer = cv2.VideoWriter(
            real_video_file, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 64)
        )
        for i in range(40):
            writer.write(np.full((64, 64, 3), i * 5, dtype=np.uint8))
        writer.release()
        shutil.copyfile(real_video_file, video_path)
        os.remove(real_video_file)

        assert video_util_process_folder_videos(folder_data) is True

        refreshed = db_get_all_videos()[0]
        assert refreshed["metadata"]["duration"] > first["metadata"]["duration"]
        assert refreshed["metadata"]["file_size"] != first["metadata"]["file_size"]
        # New poster written, superseded one cleaned up rather than orphaned
        assert refreshed["thumbnailPath"] != first["thumbnailPath"]
        assert os.path.exists(refreshed["thumbnailPath"])
        assert not os.path.exists(first["thumbnailPath"])
        assert len(os.listdir(thumb_dir)) == 1

    def test_failed_upsert_keeps_the_previous_thumbnail(
        self, test_db, test_folder_id, real_video_file, temp_media_dir, monkeypatch
    ):
        """If the write fails, the surviving row's poster must still be on disk."""
        import app.utils.videos as videos_module

        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        video_path = os.path.join(temp_media_dir, "clip.mp4")
        shutil.copyfile(real_video_file, video_path)

        folder_data = [(temp_media_dir, test_folder_id, False)]
        videos_module.video_util_process_folder_videos(folder_data)
        original = db_get_all_videos()[0]

        # Replace the source so the rescan regenerates, then fail the write
        import numpy as np

        writer = cv2.VideoWriter(
            real_video_file, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 64)
        )
        for i in range(40):
            writer.write(np.full((64, 64, 3), i * 5, dtype=np.uint8))
        writer.release()
        shutil.copyfile(real_video_file, video_path)
        os.remove(real_video_file)

        monkeypatch.setattr(
            videos_module, "db_bulk_insert_videos", lambda records: False
        )
        assert videos_module.video_util_process_folder_videos(folder_data) is False

        # Row is untouched and still points at a thumbnail that exists
        unchanged = db_get_all_videos()[0]
        assert unchanged["thumbnailPath"] == original["thumbnailPath"]
        assert os.path.exists(original["thumbnailPath"])
        # The poster written for the abandoned record is not left behind
        assert len(os.listdir(thumb_dir)) == 1

    def test_rescan_regenerates_a_missing_thumbnail(
        self, test_db, test_folder_id, real_video_file, temp_media_dir, monkeypatch
    ):
        """A deleted thumbnail file should be regenerated on the next scan."""
        from app.utils.videos import video_util_process_folder_videos

        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)

        video_path = os.path.join(temp_media_dir, "clip.mp4")
        shutil.copyfile(real_video_file, video_path)
        os.remove(real_video_file)

        folder_data = [(temp_media_dir, test_folder_id, False)]
        video_util_process_folder_videos(folder_data)
        os.remove(db_get_all_videos()[0]["thumbnailPath"])

        assert video_util_process_folder_videos(folder_data) is True
        refreshed = db_get_all_videos()[0]
        assert refreshed["thumbnailPath"] is not None
        assert os.path.exists(refreshed["thumbnailPath"])


# ##############################
# Database
# ##############################


class TestVideosDatabase:
    def test_bulk_insert_and_get_all(self, test_db, test_folder_id):
        records = [
            make_video_record("vid-1", "/videos/a.mp4", test_folder_id),
            make_video_record(
                "vid-2", "/videos/b.mp4", test_folder_id, thumbnailPath=None
            ),
        ]
        assert db_bulk_insert_videos(records) is True

        videos = db_get_all_videos()
        assert len(videos) == 2
        by_id = {v["id"]: v for v in videos}
        assert by_id["vid-2"]["thumbnailPath"] is None
        assert by_id["vid-1"]["isFavourite"] is False
        assert by_id["vid-1"]["tags"] is None

    def test_upsert_preserves_favourite(self, test_db, test_folder_id):
        record = make_video_record("vid-1", "/videos/a.mp4", test_folder_id)
        db_bulk_insert_videos([record])
        assert db_toggle_video_favourite_status("vid-1") is True

        # Re-scan inserts the same path under a new id; favourite must survive
        rescan = make_video_record("vid-new", "/videos/a.mp4", test_folder_id)
        db_bulk_insert_videos([rescan])

        videos = db_get_all_videos()
        assert len(videos) == 1
        assert videos[0]["id"] == "vid-1"
        assert videos[0]["isFavourite"] is True

    def test_upsert_keeps_old_thumbnail_when_new_is_null(self, test_db, test_folder_id):
        db_bulk_insert_videos(
            [make_video_record("vid-1", "/videos/a.mp4", test_folder_id)]
        )
        db_bulk_insert_videos(
            [
                make_video_record(
                    "vid-2", "/videos/a.mp4", test_folder_id, thumbnailPath=None
                )
            ]
        )
        videos = db_get_all_videos()
        assert videos[0]["thumbnailPath"] == "/thumbs/thumbnail_vid-1.jpg"

    def test_get_by_folder_ids_and_delete(self, test_db, test_folder_id):
        db_bulk_insert_videos(
            [make_video_record("vid-1", "/videos/a.mp4", test_folder_id)]
        )
        rows = db_get_videos_by_folder_ids([test_folder_id])
        assert len(rows) == 1
        assert rows[0][0] == "vid-1"

        assert db_delete_videos_by_ids(["vid-1"]) is True
        assert db_get_all_videos() == []

    def test_cascade_delete_with_folder(self, test_db, test_folder_id):
        db_bulk_insert_videos(
            [make_video_record("vid-1", "/videos/a.mp4", test_folder_id)]
        )
        conn = sqlite3.connect(test_db)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM folders WHERE folder_id = ?", (test_folder_id,))
        conn.commit()
        conn.close()
        assert db_get_all_videos() == []

    def test_toggle_favourite_unknown_id(self, test_db):
        assert db_toggle_video_favourite_status("nope") is False

    def test_get_video_by_id(self, test_db, test_folder_id):
        db_bulk_insert_videos(
            [make_video_record("vid-1", "/videos/a.mp4", test_folder_id)]
        )
        video = db_get_video_by_id("vid-1")
        assert video["path"] == "/videos/a.mp4"
        assert db_get_video_by_id("missing") is None


# ##############################
# Routes
# ##############################


class TestVideosAPI:
    def test_get_all_videos_empty(self, client):
        response = client.get("/videos/")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_get_all_videos(self, client, test_folder_id):
        metadata = '{"name": "a.mp4", "date_created": "2026-01-01T00:00:00", "width": 640, "height": 480, "duration": 12.5, "fps": 30.0, "file_location": "/videos/a.mp4", "file_size": 123, "item_type": "video/mp4"}'
        db_bulk_insert_videos(
            [
                make_video_record(
                    "vid-1", "/videos/a.mp4", test_folder_id, metadata=metadata
                )
            ]
        )
        response = client.get("/videos/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == "vid-1"
        assert data[0]["metadata"]["duration"] == 12.5

    def test_toggle_favourite(self, client, test_folder_id):
        db_bulk_insert_videos(
            [make_video_record("vid-1", "/videos/a.mp4", test_folder_id)]
        )
        response = client.post("/videos/toggle-favourite", json={"video_id": "vid-1"})
        assert response.status_code == 200
        assert response.json()["isFavourite"] is True

        response = client.post("/videos/toggle-favourite", json={"video_id": "vid-1"})
        assert response.json()["isFavourite"] is False

    def test_toggle_favourite_unknown_id(self, client):
        response = client.post("/videos/toggle-favourite", json={"video_id": "nope"})
        assert response.status_code == 404

    def test_toggle_favourite_error_matches_the_documented_envelope(self, client):
        """The 404 body must carry the ErrorResponse fields the route advertises."""
        response = client.post("/videos/toggle-favourite", json={"video_id": "nope"})
        assert response.status_code == 404

        detail = response.json()["detail"]
        assert detail["success"] is False
        assert detail["error"]
        assert detail["message"]

    def test_one_malformed_record_does_not_break_the_listing(
        self, client, test_folder_id
    ):
        """A row with unusable metadata is skipped, not fatal to the whole tab."""
        good_metadata = (
            '{"name": "a.mp4", "date_created": null, "width": 640, "height": 480,'
            ' "file_location": "/videos/a.mp4", "file_size": 1, "item_type": "video/mp4"}'
        )
        db_bulk_insert_videos(
            [
                make_video_record(
                    "vid-good", "/videos/a.mp4", test_folder_id, metadata=good_metadata
                ),
                make_video_record(
                    "vid-bad", "/videos/b.mp4", test_folder_id, metadata="not json"
                ),
            ]
        )

        response = client.get("/videos/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert [v["id"] for v in data] == ["vid-good"]

    def test_get_all_videos_db_error_returns_500(self, client, monkeypatch):
        def boom():
            raise RuntimeError("db down")

        monkeypatch.setattr("app.routes.videos.db_get_all_videos", boom)
        response = client.get("/videos/")
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail["success"] is False
        assert detail["error"]
        assert detail["message"]

    def test_toggle_favourite_row_disappears_after_toggle(self, client, monkeypatch):
        # Toggle reports success, but the row can't be read back -> 404
        monkeypatch.setattr(
            "app.routes.videos.db_toggle_video_favourite_status", lambda vid: True
        )
        monkeypatch.setattr("app.routes.videos.db_get_video_by_id", lambda vid: None)
        response = client.post("/videos/toggle-favourite", json={"video_id": "vid-1"})
        assert response.status_code == 404

    def test_toggle_favourite_db_error_returns_500(self, client, monkeypatch):
        def boom(vid):
            raise RuntimeError("db down")

        monkeypatch.setattr("app.routes.videos.db_toggle_video_favourite_status", boom)
        response = client.post("/videos/toggle-favourite", json={"video_id": "vid-1"})
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail["success"] is False
        assert detail["error"]
        assert detail["message"]


# ##############################
# Utility edge cases
# ##############################


class TestVideoUtilEdgeCases:
    def test_collect_superseded_skips_records_without_thumbnail(self):
        records = [{"path": "/v/a.mp4", "thumbnailPath": None}]
        already = {"/v/a.mp4": ("/thumbs/old.jpg", {})}
        assert video_util_collect_superseded_thumbnails(records, already) == []

    def test_source_is_unchanged_missing_file(self):
        assert video_util_source_is_unchanged("/nope/missing.mp4", {}) is False

    def test_remove_thumbnail_files_tolerates_os_error(
        self, temp_media_dir, monkeypatch
    ):
        thumb = os.path.join(temp_media_dir, "t.jpg")
        with open(thumb, "wb") as f:
            f.write(b"x")

        def boom(path):
            raise OSError("locked")

        monkeypatch.setattr("app.utils.videos.os.remove", boom)
        # Must swallow the error, not raise
        video_util_remove_thumbnail_files([thumb])

    def test_get_videos_from_folder_non_recursive_bad_dir(self):
        assert video_util_get_videos_from_folder("/no/such/dir", recursive=False) == []

    def test_extract_metadata_missing_file(self):
        metadata = video_util_extract_metadata("/no/such/file.mp4")
        assert metadata["file_size"] == 0
        assert metadata["width"] == 0

    def test_prepare_records_skips_when_folder_id_falsy(self, temp_media_dir):
        video_path = os.path.join(temp_media_dir, "a.mp4")
        with open(video_path, "wb") as f:
            f.write(b"data")
        # Folder resolves to id 0, which the guard treats as "no folder"
        records = video_util_prepare_video_records(
            [video_path], {os.path.abspath(temp_media_dir): 0}
        )
        assert records == []

    def test_process_folder_inner_exception_is_isolated(
        self, test_db, test_folder_id, temp_media_dir, monkeypatch
    ):
        thumb_dir = os.path.join(temp_media_dir, "thumbs")
        monkeypatch.setattr("app.utils.videos.THUMBNAIL_IMAGES_PATH", thumb_dir)
        with open(os.path.join(temp_media_dir, "a.mp4"), "wb") as f:
            f.write(b"data")

        def boom(folder_ids):
            raise RuntimeError("index read failed")

        monkeypatch.setattr("app.utils.videos.db_get_video_index_by_folder_ids", boom)
        # The inner handler swallows the error and continues -> overall success
        folder_data = [(temp_media_dir, test_folder_id, False)]
        assert video_util_process_folder_videos(folder_data) is True

    def test_process_folder_outer_exception_returns_false(self, monkeypatch):
        def boom(path, exist_ok=False):
            raise RuntimeError("mkdir failed")

        monkeypatch.setattr("app.utils.videos.os.makedirs", boom)
        assert video_util_process_folder_videos([]) is False

    def test_generate_thumbnail_returns_false_when_frame_unreadable(
        self, temp_media_dir
    ):
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.get.return_value = 0  # fps/frame_count 0 -> target 0
        cap.read.return_value = (False, None)
        out = os.path.join(temp_media_dir, "t.jpg")
        assert video_util_generate_thumbnail("x.mp4", out, capture=cap) is False

    def test_generate_thumbnail_retries_from_first_frame(self, temp_media_dir):
        import numpy as np

        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 100.0,
        }.get(prop, 0)
        # First read at the seeked frame fails; the retry from frame 0 succeeds
        cap.read.side_effect = [(False, None), (True, frame)]
        out = os.path.join(temp_media_dir, "t.jpg")
        assert video_util_generate_thumbnail("x.mp4", out, capture=cap) is True
        assert os.path.exists(out)

    def test_generate_thumbnail_swallows_exceptions(self, temp_media_dir):
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.get.return_value = 0
        cap.read.side_effect = RuntimeError("decode boom")
        out = os.path.join(temp_media_dir, "t.jpg")
        assert video_util_generate_thumbnail("x.mp4", out, capture=cap) is False

    def test_extract_metadata_swallows_capture_errors(self, temp_media_dir):
        real = os.path.join(temp_media_dir, "a.mp4")
        with open(real, "wb") as f:
            f.write(b"data")
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.get.side_effect = RuntimeError("prop boom")
        metadata = video_util_extract_metadata(real, capture=cap)
        assert metadata["file_size"] > 0  # os.stat ran before the capture error
        assert metadata["width"] == 0  # capture error left the defaults
