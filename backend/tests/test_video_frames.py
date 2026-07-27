import json
import os
import sqlite3
import tempfile
import shutil

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database.video_frames import (
    db_bulk_insert_video_frames,
    db_clear_frame_paths,
    db_create_video_frames_tables,
    db_get_all_frame_embeddings,
    db_get_frame_embeddings_for_video,
    db_get_unembedded_video_frames,
    db_get_untagged_videos,
    db_get_video_ids_by_tag,
    db_get_video_tags,
    db_get_videos_needing_scoring,
    db_mark_video_frames_embedded,
    db_mark_videos_tagged,
    db_upsert_video_frame_embeddings,
    db_write_video_classes,
    db_write_video_semantic_scores,
)
from app.database.videos import db_bulk_insert_videos, db_create_videos_table
from app.routes.videos import router as videos_router
from app.utils.videos import (
    video_util_aggregate_frame_classes,
    video_util_extract_video_frames,
    video_util_purge_frame_cache,
    video_util_sample_frame_timestamps,
)

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Point every module that touches these tables at a fresh tempfile
    database. video_frames borrows images._connect, so that module's
    DATABASE_PATH has to be patched too."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.videos.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    from app.database.folders import db_create_folders_table
    from app.database.yolo_mapping import db_create_YOLO_classes_table

    db_create_folders_table()
    db_create_YOLO_classes_table()
    db_create_videos_table()
    db_create_video_frames_tables()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def frames_dir(monkeypatch):
    """Redirect the frame cache at a temp dir so tests never touch the real
    user data directory."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr("app.utils.videos.VIDEO_FRAMES_PATH", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def tagging_folder_id(test_db):
    """A folder with AI tagging enabled, so its videos are pickable."""
    folder_id = "folder-ai-on"
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, AI_Tagging) "
        "VALUES (?, ?, 0, 1)",
        (folder_id, os.path.abspath("tagging-folder")),
    )
    conn.commit()
    conn.close()
    return folder_id


@pytest.fixture
def video_id(tagging_folder_id):
    video = {
        "id": "vid-1",
        "path": os.path.abspath("tagging-folder/clip.mp4"),
        "folder_id": tagging_folder_id,
        "thumbnailPath": "/thumbs/thumbnail_vid-1.jpg",
        "metadata": json.dumps(
            {
                "name": "clip.mp4",
                "date_created": "2026-01-01T00:00:00",
                "width": 1920,
                "height": 1080,
                "duration": 30.0,
                "fps": 30.0,
                "file_location": "clip.mp4",
                "file_size": 1024,
                "item_type": "video/mp4",
            }
        ),
        "isTagged": False,
        "captured_at": "2026-01-01T00:00:00",
    }
    db_bulk_insert_videos([video])
    return video["id"]


@pytest.fixture
def temp_media_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def real_video_file(temp_media_dir):
    """A 3-second video: long enough that a 1s interval yields several frames."""
    video_path = os.path.join(temp_media_dir, "sample.avi")
    writer = cv2.VideoWriter(
        video_path, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 64)
    )
    if not writer.isOpened():
        pytest.skip("cv2.VideoWriter unavailable in this environment")
    for i in range(30):
        writer.write(np.full((64, 64, 3), (i * 8) % 256, dtype=np.uint8))
    writer.release()
    return video_path


@pytest.fixture
def client(test_db):
    app = FastAPI()
    app.include_router(videos_router, prefix="/videos")
    return TestClient(app)


def insert_frames(video_id, count, frames_dir=None):
    """Insert `count` frame rows, one second apart."""
    records = [
        {
            "id": f"{video_id}-frame-{i}",
            "video_id": video_id,
            "frame_path": os.path.join(frames_dir or "/frames", f"f{i}.jpg"),
            "timestamp_sec": float(i),
            "frame_index": i,
        }
        for i in range(count)
    ]
    db_bulk_insert_video_frames(records)
    return records


# ##############################
# Sampling strategy
# ##############################


class TestSampleFrameTimestamps:
    def test_samples_at_chunk_midpoints(self):
        # 20s at 5s intervals: 2.5, 7.5, 12.5, 17.5 -- never the leading frame,
        # which is often black.
        assert video_util_sample_frame_timestamps(20.0, 5.0, 200) == [
            2.5,
            7.5,
            12.5,
            17.5,
        ]

    def test_ten_minute_video_at_five_seconds(self):
        assert len(video_util_sample_frame_timestamps(600.0, 5.0, 200)) == 120

    def test_long_video_stretches_interval_instead_of_frame_count(self):
        timestamps = video_util_sample_frame_timestamps(3 * 3600.0, 5.0, 200)
        assert len(timestamps) == 200
        # 3 hours over 200 frames = one frame per 54 seconds.
        assert timestamps[1] - timestamps[0] == pytest.approx(54.0)

    def test_video_shorter_than_the_interval_yields_one_midpoint_frame(self):
        assert video_util_sample_frame_timestamps(3.0, 5.0, 200) == [1.5]

    @pytest.mark.parametrize("duration", [None, 0, -1])
    def test_unknown_duration_falls_back_to_a_single_frame(self, duration):
        assert video_util_sample_frame_timestamps(duration, 5.0, 200) == [0.0]

    def test_respects_the_cap_exactly(self):
        assert len(video_util_sample_frame_timestamps(100.0, 1.0, 10)) == 10


# ##############################
# Aggregating frames into video tags
# ##############################


class TestAggregateFrameClasses:
    def test_drops_classes_seen_in_too_few_frames(self):
        frames = [[0]] * 4 + [[15]]  # person in 4 frames, cat in 1
        assert video_util_aggregate_frame_classes(frames, 2) == [(0, 4)]

    def test_counts_a_class_once_per_frame(self):
        # Three people in one frame is still one frame of support.
        frames = [[0, 0, 0], [0, 0]]
        assert video_util_aggregate_frame_classes(frames, 2) == [(0, 2)]

    def test_short_videos_relax_the_support_requirement(self):
        # Two frames can never reach a support of 2 for a class in one of them,
        # so the requirement drops to 1 rather than tagging nothing.
        assert video_util_aggregate_frame_classes([[0], [15]], 2) == [(0, 1), (15, 1)]

    def test_orders_by_frame_count_descending(self):
        frames = [[0], [0, 15], [0, 15], [15]]
        assert video_util_aggregate_frame_classes(frames, 2) == [(0, 3), (15, 3)]

    def test_no_frames_means_no_tags(self):
        assert video_util_aggregate_frame_classes([], 2) == []


# ##############################
# Frame extraction
# ##############################


class TestExtractVideoFrames:
    def test_writes_a_jpeg_per_sampled_timestamp(self, real_video_file, frames_dir):
        records = video_util_extract_video_frames("vid-1", real_video_file, 1.0)

        assert len(records) == 3  # 3 seconds of footage at 1s intervals
        for record in records:
            assert os.path.exists(record["frame_path"])
            assert record["video_id"] == "vid-1"
        assert [r["frame_index"] for r in records] == [0, 1, 2]

    def test_frames_are_downscaled(self, real_video_file, frames_dir, monkeypatch):
        monkeypatch.setattr("app.config.settings.VIDEO_FRAME_MAX_DIMENSION", 32)
        records = video_util_extract_video_frames("vid-1", real_video_file, 1.0)

        frame = cv2.imread(records[0]["frame_path"])
        assert max(frame.shape[:2]) <= 32

    def test_resampling_replaces_the_previous_frames(self, real_video_file, frames_dir):
        dense = video_util_extract_video_frames("vid-1", real_video_file, 1.0)
        sparse = video_util_extract_video_frames("vid-1", real_video_file, 10.0)

        assert len(sparse) < len(dense)
        # The old dense sample is gone rather than left behind as orphans.
        frame_dir = os.path.join(frames_dir, "vid-1")
        assert len(os.listdir(frame_dir)) == len(sparse)

    def test_undecodable_file_yields_no_frames(self, temp_media_dir, frames_dir):
        broken = os.path.join(temp_media_dir, "broken.mp4")
        with open(broken, "wb") as f:
            f.write(b"not a video")

        assert video_util_extract_video_frames("vid-1", broken, 5.0) == []


# ##############################
# Database round-trips
# ##############################


class TestVideoFrameDatabase:
    def test_untagged_videos_only_from_ai_tagging_folders(self, video_id):
        assert [v["id"] for v in db_get_untagged_videos()] == [video_id]

        db_mark_videos_tagged([video_id])
        assert db_get_untagged_videos() == []

    def test_frames_cascade_when_their_video_is_deleted(self, video_id, test_db):
        insert_frames(video_id, 3)

        from app.database.videos import db_delete_videos_by_ids

        db_delete_videos_by_ids([video_id])

        conn = sqlite3.connect(test_db)
        count = conn.execute("SELECT COUNT(*) FROM video_frames").fetchone()[0]
        conn.close()
        assert count == 0

    def test_embedded_frames_drop_out_of_the_pending_list(self, video_id):
        frames = insert_frames(video_id, 3)
        assert len(db_get_unembedded_video_frames()) == 3

        db_mark_video_frames_embedded([frames[0]["id"]])
        assert len(db_get_unembedded_video_frames()) == 2

    def test_purged_frames_are_not_re_embedded(self, video_id):
        insert_frames(video_id, 3)
        db_clear_frame_paths()

        # Nothing on disk to read, so they must not come back as pending work.
        assert db_get_unembedded_video_frames() == []

    def test_semantic_rescoring_leaves_yolo_tags_alone(self, video_id, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO mappings (class_id, name) VALUES (1000, 'sunset')")
        conn.commit()
        conn.close()

        db_write_video_classes(video_id, [(0, 4)])
        db_write_video_semantic_scores(video_id, [(1000, 0.9, 3)], "sig-1")
        assert sorted(db_get_video_tags([video_id])[video_id]) == [
            "person",
            "sunset",
        ]

        # A vocabulary change rewrites the semantic rows only.
        db_write_video_semantic_scores(video_id, [], "sig-2")
        assert db_get_video_tags([video_id])[video_id] == ["person"]

    def test_tag_lookup_is_case_insensitive(self, video_id):
        db_write_video_classes(video_id, [(0, 4)])

        assert db_get_video_ids_by_tag("PERSON") == [video_id]
        assert db_get_video_ids_by_tag("giraffe") == []

    def test_embeddings_round_trip_per_video_and_globally(self, video_id):
        frames = insert_frames(video_id, 2)
        db_upsert_video_frame_embeddings(
            [
                (frames[0]["id"], "m1", np.array([1.0, 0.0], dtype=np.float32)),
                (frames[1]["id"], "m1", np.array([0.0, 1.0], dtype=np.float32)),
            ]
        )

        matrix = db_get_frame_embeddings_for_video(video_id, "m1")
        assert matrix.shape == (2, 2)

        video_ids, timestamps, all_matrix = db_get_all_frame_embeddings("m1")
        assert video_ids == [video_id, video_id]
        assert timestamps == [0.0, 1.0]
        assert all_matrix.shape == (2, 2)

    def test_scoring_signature_gates_rework(self, video_id):
        frames = insert_frames(video_id, 1)
        db_upsert_video_frame_embeddings(
            [(frames[0]["id"], "m1", np.array([1.0, 0.0], dtype=np.float32))]
        )

        assert db_get_videos_needing_scoring("m1", "sig-1", 10) == [video_id]

        db_write_video_semantic_scores(video_id, [], "sig-1")
        assert db_get_videos_needing_scoring("m1", "sig-1", 10) == []
        # A vocabulary change invalidates the stamp and the work comes back.
        assert db_get_videos_needing_scoring("m1", "sig-2", 10) == [video_id]


# ##############################
# Purging the frame cache
# ##############################


class TestPurgeFrameCache:
    def test_removes_jpegs_but_keeps_tags_and_embeddings(
        self, video_id, real_video_file, frames_dir
    ):
        frames = video_util_extract_video_frames("vid-1", real_video_file, 1.0)
        db_bulk_insert_video_frames(frames)
        db_upsert_video_frame_embeddings(
            [(frames[0]["id"], "m1", np.array([1.0, 0.0], dtype=np.float32))]
        )
        db_write_video_classes(video_id, [(0, 3)])

        reclaimed = video_util_purge_frame_cache()

        assert reclaimed > 0
        assert not os.path.exists(frames_dir)
        # The index survives the cache: tags and semantic search keep working.
        assert db_get_video_tags([video_id])[video_id] == ["person"]
        assert db_get_frame_embeddings_for_video(video_id, "m1").shape == (1, 2)

    def test_purging_an_empty_cache_is_harmless(self, test_db, frames_dir):
        shutil.rmtree(frames_dir, ignore_errors=True)
        assert video_util_purge_frame_cache() == 0


# ##############################
# Routes
# ##############################


class TestVideoTagRoutes:
    def test_get_all_videos_returns_tags(self, client, video_id):
        db_write_video_classes(video_id, [(0, 4)])

        response = client.get("/videos/")

        assert response.status_code == 200
        assert response.json()["data"][0]["tags"] == ["person"]

    def test_untagged_video_reports_null_tags(self, client, video_id):
        response = client.get("/videos/")

        assert response.json()["data"][0]["tags"] is None

    def test_search_by_tag(self, client, video_id):
        db_write_video_classes(video_id, [(0, 4)])

        response = client.get("/videos/search", params={"tag": "person"})

        assert response.status_code == 200
        assert [v["id"] for v in response.json()["data"]] == [video_id]

    def test_search_by_tag_with_no_matches(self, client, video_id):
        response = client.get("/videos/search", params={"tag": "person"})

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_semantic_search_without_models_returns_404(
        self, client, video_id, monkeypatch
    ):
        monkeypatch.setattr(
            "app.models.model_registry.get_model_path",
            lambda key: "/nonexistent/model.onnx",
        )

        response = client.get("/videos/semantic-search", params={"query": "a beach"})

        assert response.status_code == 404
        assert "not installed" in response.json()["detail"]["message"]

    def test_purge_route_reports_bytes_reclaimed(
        self, client, video_id, real_video_file, frames_dir
    ):
        db_bulk_insert_video_frames(
            video_util_extract_video_frames("vid-1", real_video_file, 1.0)
        )

        response = client.post("/videos/purge-frame-cache")

        assert response.status_code == 200
        assert response.json()["bytes_reclaimed"] > 0
