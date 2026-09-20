import json
import os
import sqlite3
import tempfile
from contextlib import closing
from types import SimpleNamespace
from typing import Callable, Dict, Iterator, List, Optional
from unittest.mock import patch

import numpy as np
import pytest

from app.models.FaceDetector import FaceDetectionResult
from app.utils.videos import (
    VideoFace,
    video_util_backfill_video_faces,
    video_util_detect_video_faces,
    video_util_expected_frame_dimension,
    video_util_face_detection_enabled,
    video_util_frame_needs_refresh,
    video_util_process_untagged_videos,
    video_util_refresh_frame_images,
    video_util_select_video_faces,
)

# Unit vectors: A and B are different people, A_AGAIN is A in a neighbouring
# keyframe (cosine 0.995 with A, above the 0.92 dedupe threshold).
A = np.eye(128, dtype=np.float32)[0]
B = np.eye(128, dtype=np.float32)[1]
A_AGAIN = (A + 0.1 * np.eye(128, dtype=np.float32)[2]) / np.sqrt(1.01)


def _face(embedding: np.ndarray, confidence: float, frame_id: str = "f") -> VideoFace:
    return VideoFace(
        frame_id=frame_id,
        embedding=embedding,
        bbox={"x": 0, "y": 0, "width": 50, "height": 50},
        confidence=confidence,
    )


def _result(*faces: tuple) -> FaceDetectionResult:
    """A detector result from (embedding, confidence) pairs."""
    return FaceDetectionResult(
        embeddings=[embedding for embedding, _ in faces],
        bboxes=[
            {"x": i * 60, "y": 0, "width": 50, "height": 50} for i in range(len(faces))
        ],
        confidences=[confidence for _, confidence in faces],
        faces_skipped=0,
    )


def _frames(video_id: str, count: int, generation: str = "") -> List[dict]:
    """Keyframe records shaped like video_util_extract_video_frames returns."""
    return [
        {
            "id": f"{video_id}-f{i}{generation}",
            "video_id": video_id,
            "frame_path": f"/frames/{video_id}/frame_{i:04d}.jpg",
            "timestamp_sec": i * 5.0 + 2.5,
            "frame_index": i,
        }
        for i in range(count)
    ]


# ##############################
# Choosing which faces to keep
# ##############################


class TestFaceDetectionPreference:
    """Opt-in from Settings, with the config value as the fallback."""

    @pytest.mark.parametrize("stored", [True, False])
    def test_the_setting_from_settings_wins_over_the_default(self, stored):
        with (
            patch(
                "app.database.metadata.db_get_metadata",
                return_value={"user_preferences": {"Video_Face_Detection": stored}},
            ),
            patch("app.config.settings.VIDEO_FACE_DETECTION", not stored),
        ):
            assert video_util_face_detection_enabled() is stored

    @pytest.mark.parametrize("default", [True, False])
    def test_falls_back_when_the_user_never_chose(self, default):
        with (
            patch("app.database.metadata.db_get_metadata", return_value={}),
            patch("app.config.settings.VIDEO_FACE_DETECTION", default),
        ):
            assert video_util_face_detection_enabled() is default

    def test_an_unreadable_preference_does_not_break_tagging(self):
        with (
            patch(
                "app.database.metadata.db_get_metadata",
                side_effect=RuntimeError("no database"),
            ),
            patch("app.config.settings.VIDEO_FACE_DETECTION", False),
        ):
            assert video_util_face_detection_enabled() is False


class TestSelectVideoFaces:
    def test_drops_near_duplicates_keeping_the_most_confident(self):
        kept = video_util_select_video_faces(
            [_face(A, 0.7, "f1"), _face(A_AGAIN, 0.9, "f2"), _face(B, 0.8, "f3")],
            dedupe_threshold=0.92,
            max_faces=40,
        )
        assert [face["frame_id"] for face in kept] == ["f2", "f3"]

    def test_keeps_every_distinct_person(self):
        kept = video_util_select_video_faces(
            [_face(A, 0.9), _face(B, 0.8)], dedupe_threshold=0.92, max_faces=40
        )
        assert len(kept) == 2

    def test_caps_a_crowd_keeping_the_most_confident(self):
        people = [_face(np.eye(128)[i], 0.1 * (i + 1)) for i in range(5)]

        kept = video_util_select_video_faces(people, dedupe_threshold=0.92, max_faces=2)

        assert [face["confidence"] for face in kept] == pytest.approx([0.5, 0.4])

    def test_no_faces_is_no_faces(self):
        assert video_util_select_video_faces([], 0.92, 40) == []


# ##############################
# Scanning keyframes
# ##############################


class TestDetectVideoFaces:
    def test_scans_only_keyframes_with_a_person(self):
        calls: List[str] = []
        detector = SimpleNamespace(detect_faces=calls.append)  # records, finds none

        video_util_detect_video_faces(detector, _frames("v", 3), [[0], [2], [0, 56]])

        assert calls == ["/frames/v/frame_0000.jpg", "/frames/v/frame_0002.jpg"]

    def test_faces_remember_their_keyframe(self):
        detector = SimpleNamespace(
            detect_faces=lambda path: _result((A, 0.9), (B, 0.7))
        )

        faces = video_util_detect_video_faces(detector, _frames("v", 1), [[0]])

        assert [face["frame_id"] for face in faces] == ["v-f0", "v-f0"]
        assert [face["confidence"] for face in faces] == [0.9, 0.7]
        assert faces[1]["bbox"]["x"] == 60
        assert faces[1]["embedding"] is B

    def test_unreadable_keyframe_is_skipped(self):
        detector = SimpleNamespace(detect_faces=lambda path: None)
        assert video_util_detect_video_faces(detector, _frames("v", 1), [[0]]) == []


# ##############################
# The tagging pass, against a real database
# ##############################


@pytest.fixture
def test_db(monkeypatch) -> Iterator[str]:
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    for module in (
        "app.config.settings",
        "app.database.images",
        "app.database.videos",
        "app.database.folders",
        "app.database.yolo_mapping",
        "app.database.faces",
        "app.database.face_clusters",
    ):
        monkeypatch.setattr(f"{module}.DATABASE_PATH", db_path)

    from app.database.face_clusters import db_create_clusters_table
    from app.database.faces import db_create_faces_table
    from app.database.folders import db_create_folders_table
    from app.database.images import db_create_images_table
    from app.database.video_frames import db_create_video_frames_tables
    from app.database.videos import db_create_videos_table
    from app.database.yolo_mapping import db_create_YOLO_classes_table

    # images too, though nothing here is a photo: with FKs on, SQLite resolves
    # every parent of faces when a keyframe delete cascades into it.
    db_create_folders_table()
    db_create_YOLO_classes_table()
    db_create_images_table()
    db_create_videos_table()
    db_create_video_frames_tables()
    db_create_clusters_table()
    db_create_faces_table()

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging) VALUES ('folder-1', '/videos', 0, 1)"
        )
        conn.commit()

    yield db_path
    os.unlink(db_path)


def _add_video(
    db_path: str, video_id: str, is_tagged: int = 0, width: int = 1920
) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO videos (id, path, folder_id, isTagged, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                video_id,
                f"/videos/{video_id}.mp4",
                "folder-1",
                is_tagged,
                json.dumps({"width": width, "height": 1080}),
            ),
        )
        conn.commit()


def _rows(db_path: str, sql: str) -> list:
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute(sql).fetchall()


@pytest.fixture
def run_pass(test_db) -> Iterator[Callable[..., SimpleNamespace]]:
    """Run the real tagging pass with the models and frame extraction mocked.

    Takes per-video keyframes, per-keyframe classes and per-path detector
    results; returns the mocked models for inspection.
    """

    def run(
        frames: Dict[str, List[dict]],
        classes: Dict[str, List[int]],
        detections: Dict[str, Optional[FaceDetectionResult]],
        on_detect: Optional[Callable[[str], None]] = None,
        face_detection: bool = True,
    ) -> SimpleNamespace:
        def detect(path: str) -> Optional[FaceDetectionResult]:
            if on_detect:
                on_detect(path)
            return detections.get(path)

        with (
            patch(
                "app.utils.videos.video_util_extract_video_frames",
                side_effect=lambda video_id, path, interval: frames[video_id],
            ),
            patch("app.utils.videos.video_util_get_frame_interval", return_value=5.0),
            patch("app.config.settings.VIDEO_FACE_DETECTION", face_detection),
            patch("app.models.ObjectClassifier.ObjectClassifier") as classifier_cls,
            patch("app.models.FaceDetector.FaceDetector") as detector_cls,
        ):
            classifier_cls.return_value.get_classes.side_effect = classes.get
            detector_cls.return_value.detect_faces.side_effect = detect
            ok = video_util_process_untagged_videos()
        return SimpleNamespace(
            ok=ok,
            classifier=classifier_cls.return_value,
            detector_cls=detector_cls,
            detector=detector_cls.return_value,
        )

    yield run


class TestVideoFacePass:
    def test_stores_deduplicated_faces_against_their_keyframes(self, test_db, run_pass):
        _add_video(test_db, "vid-1")
        frames = _frames("vid-1", 3)
        paths = [f["frame_path"] for f in frames]

        run = run_pass(
            {"vid-1": frames},
            {paths[0]: [0], paths[1]: [2], paths[2]: [0]},
            {paths[0]: _result((A, 0.9)), paths[2]: _result((A_AGAIN, 0.8), (B, 0.85))},
        )

        assert run.ok
        # A_AGAIN is A in a later keyframe, so it is dropped as a duplicate.
        assert sorted(_rows(test_db, "SELECT image_id, frame_id FROM faces")) == [
            (None, "vid-1-f0"),
            (None, "vid-1-f2"),
        ]
        assert _rows(test_db, "SELECT isTagged FROM videos") == [(1,)]
        run.classifier.close.assert_called_once()
        run.detector.close.assert_called_once()

    def test_switched_off_the_face_models_never_load(self, test_db, run_pass):
        """The default until keyframe faces are safe to cluster; object tagging
        must carry on exactly as before."""
        _add_video(test_db, "vid-1")
        frames = _frames("vid-1", 1)
        path = frames[0]["frame_path"]

        run = run_pass(
            {"vid-1": frames},
            {path: [0]},
            {path: _result((A, 0.9))},
            face_detection=False,
        )

        assert run.ok
        run.detector_cls.assert_not_called()
        assert _rows(test_db, "SELECT COUNT(*) FROM faces") == [(0,)]
        assert _rows(test_db, "SELECT class_id FROM video_classes") == [(0,)]
        assert _rows(test_db, "SELECT isTagged FROM videos") == [(1,)]

    def test_videos_without_people_store_no_faces(self, test_db, run_pass):
        _add_video(test_db, "vid-1")
        frames = _frames("vid-1", 2)

        run = run_pass({"vid-1": frames}, {f["frame_path"]: [2] for f in frames}, {})

        run.detector.detect_faces.assert_not_called()
        assert _rows(test_db, "SELECT COUNT(*) FROM faces") == [(0,)]
        assert _rows(test_db, "SELECT isTagged FROM videos") == [(1,)]

    def test_retagging_replaces_faces_instead_of_adding_more(self, test_db, run_pass):
        """A re-tag resamples with fresh keyframe ids; the old keyframes' faces
        must go with them, not accumulate."""
        _add_video(test_db, "vid-1")
        for generation in ("", "-again"):
            frames = _frames("vid-1", 1, generation)
            path = frames[0]["frame_path"]
            run_pass({"vid-1": frames}, {path: [0]}, {path: _result((A, 0.9))})
            with closing(sqlite3.connect(test_db)) as conn:
                conn.execute("UPDATE videos SET isTagged = 0")
                conn.commit()

        assert _rows(test_db, "SELECT frame_id FROM faces") == [("vid-1-f0-again",)]

    def test_video_deleted_mid_pass_does_not_stop_the_rest(self, test_db, run_pass):
        """Inference is slow, so a folder can be removed while its videos are
        being tagged; the next video must still get its faces."""
        _add_video(test_db, "vid-gone")
        _add_video(test_db, "vid-kept")
        gone, kept = _frames("vid-gone", 1), _frames("vid-kept", 1)
        gone_path, kept_path = gone[0]["frame_path"], kept[0]["frame_path"]

        def delete_gone_video(path: str) -> None:
            if path == gone_path:
                with closing(sqlite3.connect(test_db)) as conn:
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.execute("DELETE FROM videos WHERE id = 'vid-gone'")
                    conn.commit()

        run = run_pass(
            {"vid-gone": gone, "vid-kept": kept},
            {gone_path: [0], kept_path: [0]},
            {gone_path: _result((A, 0.9)), kept_path: _result((B, 0.9))},
            on_detect=delete_gone_video,
        )

        assert run.ok
        assert _rows(test_db, "SELECT frame_id FROM faces") == [("vid-kept-f0",)]
        assert _rows(test_db, "SELECT id, isTagged FROM videos") == [("vid-kept", 1)]

    def test_tagging_with_detection_on_marks_the_video_scanned(self, test_db, run_pass):
        _add_video(test_db, "vid-1")
        frames = _frames("vid-1", 1)
        path = frames[0]["frame_path"]

        run_pass({"vid-1": frames}, {path: [0]}, {path: _result((A, 0.9))})

        assert _rows(test_db, "SELECT facesScanned FROM videos") == [(1,)]

    def test_tagging_with_detection_off_leaves_it_for_a_later_scan(
        self, test_db, run_pass
    ):
        """Marking it scanned here would hide the video from the backfill for
        good, so turning the setting on later could never reach it."""
        _add_video(test_db, "vid-1")
        frames = _frames("vid-1", 1)
        path = frames[0]["frame_path"]

        run_pass(
            {"vid-1": frames},
            {path: [0]},
            {path: _result((A, 0.9))},
            face_detection=False,
        )

        assert _rows(test_db, "SELECT isTagged, facesScanned FROM videos") == [(1, 0)]


# ##############################
# Deciding which keyframes are stale
# ##############################


class TestExpectedFrameDimension:
    def test_caps_a_large_source_at_the_configured_maximum(self):
        with patch("app.config.settings.VIDEO_FRAME_MAX_DIMENSION", 1280):
            metadata = {"width": 3840, "height": 2160}
            assert video_util_expected_frame_dimension(metadata) == 1280

    def test_a_small_source_can_only_give_its_own_size(self):
        # Otherwise every low-resolution video reads as permanently stale and
        # is re-sampled by every scan for nothing.
        with patch("app.config.settings.VIDEO_FRAME_MAX_DIMENSION", 1280):
            metadata = {"width": 640, "height": 480}
            assert video_util_expected_frame_dimension(metadata) == 640

    @pytest.mark.parametrize("metadata", [{}, {"width": 0, "height": 0}])
    def test_unknown_dimensions_fall_back_to_the_maximum(self, metadata):
        with patch("app.config.settings.VIDEO_FRAME_MAX_DIMENSION", 1280):
            assert video_util_expected_frame_dimension(metadata) == 1280


def _jpeg(path: str, size: tuple) -> str:
    from PIL import Image

    Image.new("RGB", size).save(path, "JPEG")
    return path


class TestFrameNeedsRefresh:
    def test_a_frame_below_what_the_source_allows_is_stale(self, tmp_path):
        path = _jpeg(str(tmp_path / "small.jpg"), (640, 360))
        assert video_util_frame_needs_refresh(path, 1280) is True

    def test_a_frame_at_full_size_is_current(self, tmp_path):
        path = _jpeg(str(tmp_path / "big.jpg"), (1280, 720))
        assert video_util_frame_needs_refresh(path, 1280) is False

    def test_a_purged_frame_has_nothing_to_read(self):
        assert video_util_frame_needs_refresh(None, 1280) is True

    def test_a_missing_file_is_stale(self, tmp_path):
        assert video_util_frame_needs_refresh(str(tmp_path / "gone.jpg"), 1280) is True

    def test_an_unreadable_file_is_stale(self, tmp_path):
        path = str(tmp_path / "broken.jpg")
        with open(path, "wb") as handle:
            handle.write(b"not a jpeg")
        assert video_util_frame_needs_refresh(path, 1280) is True


# ##############################
# Re-sampling keyframes in place
# ##############################


@pytest.fixture
def frames_dir(monkeypatch, tmp_path) -> str:
    """Keep re-sampled JPEGs out of the real user data directory."""
    path = str(tmp_path / "video_frames")
    monkeypatch.setattr("app.utils.videos.VIDEO_FRAMES_PATH", path)
    return path


@pytest.fixture
def real_video_file(tmp_path) -> str:
    """A 3-second 320x240 clip, large enough to tell resolutions apart."""
    import cv2

    video_path = str(tmp_path / "clip.avi")
    writer = cv2.VideoWriter(
        video_path, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (320, 240)
    )
    if not writer.isOpened():
        pytest.skip("cv2.VideoWriter unavailable in this environment")
    for i in range(30):
        writer.write(np.full((240, 320, 3), (i * 8) % 256, dtype=np.uint8))
    writer.release()
    return video_path


def _frame_row(frame_id: str, path: Optional[str], index: int = 0) -> dict:
    return {
        "id": frame_id,
        "video_id": "vid-1",
        "frame_path": path,
        "timestamp_sec": 1.0,
        "frame_index": index,
    }


class TestRefreshFrameImages:
    def test_rewrites_a_small_frame_at_full_size(self, tmp_path, real_video_file):
        from PIL import Image

        path = _jpeg(str(tmp_path / "frame_0000.jpg"), (64, 48))

        usable = video_util_refresh_frame_images(
            "vid-1", real_video_file, [_frame_row("f0", path)], 320
        )

        assert [frame["frame_path"] for frame in usable] == [path]
        with Image.open(path) as image:
            assert max(image.size) == 320

    def test_leaves_current_frames_alone(self, tmp_path, real_video_file):
        path = _jpeg(str(tmp_path / "frame_0000.jpg"), (320, 240))
        before = os.path.getmtime(path)
        frames = [_frame_row("f0", path)]

        usable = video_util_refresh_frame_images("vid-1", real_video_file, frames, 320)

        assert usable == frames
        assert os.path.getmtime(path) == before

    def test_a_purged_frame_is_written_back_and_recorded(
        self, test_db, frames_dir, real_video_file
    ):
        """A purged row has no path left, so one is derived from its index and
        stored -- otherwise the row still reads as purged afterwards."""
        from app.database.video_frames import (
            db_bulk_insert_video_frames,
            db_get_frames_for_video,
        )

        _add_video(test_db, "vid-1")
        db_bulk_insert_video_frames([_frame_row("f0", None, index=3)])

        usable = video_util_refresh_frame_images(
            "vid-1", real_video_file, [_frame_row("f0", None, index=3)], 320
        )

        assert usable[0]["frame_path"].endswith("frame_0003.jpg")
        assert os.path.exists(usable[0]["frame_path"])
        stored = db_get_frames_for_video("vid-1")[0]["frame_path"]
        assert stored == usable[0]["frame_path"]

    def test_an_undecodable_video_keeps_the_frames_already_on_disk(self, tmp_path):
        good = _jpeg(str(tmp_path / "good.jpg"), (320, 240))
        broken = str(tmp_path / "not-a-video.mp4")
        with open(broken, "wb") as handle:
            handle.write(b"junk")

        usable = video_util_refresh_frame_images(
            "vid-1",
            broken,
            [_frame_row("f0", good), _frame_row("f1", None, index=1)],
            320,
        )

        assert [frame["id"] for frame in usable] == ["f0"]


# ##############################
# Backfilling videos tagged before the setting existed
# ##############################


def _add_frames(video_id: str, count: int, purged: bool = False) -> List[dict]:
    from app.database.video_frames import (
        db_bulk_insert_video_frames,
        db_clear_frame_paths,
    )

    records = _frames(video_id, count)
    db_bulk_insert_video_frames(records)
    if purged:
        db_clear_frame_paths()
        return [{**record, "frame_path": None} for record in records]
    return records


@pytest.fixture
def run_scan(test_db) -> Iterator[Callable[..., SimpleNamespace]]:
    """Run the real backfill with the models and re-sampling mocked.

    Re-sampling is a no-op, so a test supplies keyframes as if they were
    already at full resolution.
    """

    def run(
        classes: Dict[str, List[int]],
        detections: Dict[str, Optional[FaceDetectionResult]],
        on_detect: Optional[Callable[[str], None]] = None,
        face_detection: bool = True,
    ) -> SimpleNamespace:
        def detect(path: str) -> Optional[FaceDetectionResult]:
            if on_detect:
                on_detect(path)
            return detections.get(path)

        with (
            patch(
                "app.utils.videos.video_util_refresh_frame_images",
                side_effect=lambda video_id, path, frames, dimension: frames,
            ) as refresh,
            patch("app.config.settings.VIDEO_FACE_DETECTION", face_detection),
            patch("app.models.ObjectClassifier.ObjectClassifier") as classifier_cls,
            patch("app.models.FaceDetector.FaceDetector") as detector_cls,
        ):
            classifier_cls.return_value.get_classes.side_effect = classes.get
            detector_cls.return_value.detect_faces.side_effect = detect
            scanned = video_util_backfill_video_faces()
        return SimpleNamespace(
            scanned=scanned,
            refresh=refresh,
            classifier=classifier_cls.return_value,
            detector_cls=detector_cls,
            detector=detector_cls.return_value,
        )

    yield run


class TestBackfillVideoFaces:
    def test_finds_people_in_a_video_tagged_before_the_setting(self, test_db, run_scan):
        _add_video(test_db, "vid-1", is_tagged=1)
        frames = _add_frames("vid-1", 3)
        paths = [frame["frame_path"] for frame in frames]

        run = run_scan(
            {paths[0]: [0], paths[1]: [2], paths[2]: [0]},
            {paths[0]: _result((A, 0.9)), paths[2]: _result((B, 0.85))},
        )

        assert run.scanned == 1
        # Faces hang off the keyframes that were already there, so the SigLIP2
        # embeddings on those rows survive the scan.
        assert sorted(_rows(test_db, "SELECT image_id, frame_id FROM faces")) == [
            (None, "vid-1-f0"),
            (None, "vid-1-f2"),
        ]
        assert _rows(test_db, "SELECT facesScanned FROM videos") == [(1,)]
        run.classifier.close.assert_called_once()
        run.detector.close.assert_called_once()

    def test_only_keyframes_with_a_person_are_resampled(self, test_db, run_scan):
        """Decoding is most of the cost, so frames that cannot hold a face must
        never be re-sampled."""
        _add_video(test_db, "vid-1", is_tagged=1)
        frames = _add_frames("vid-1", 3)
        paths = [frame["frame_path"] for frame in frames]

        run = run_scan({paths[0]: [0], paths[1]: [2], paths[2]: [19]}, {})

        resampled = run.refresh.call_args.args[2]
        assert [frame["id"] for frame in resampled] == ["vid-1-f0"]

    def test_untagged_and_already_scanned_videos_are_left_alone(
        self, test_db, run_scan
    ):
        # Untagged: the tagging pass detects faces as part of tagging it.
        _add_video(test_db, "vid-untagged")
        _add_frames("vid-untagged", 1)
        _add_video(test_db, "vid-done", is_tagged=1)
        _add_frames("vid-done", 1)
        with closing(sqlite3.connect(test_db)) as conn:
            conn.execute("UPDATE videos SET facesScanned = 1 WHERE id = 'vid-done'")
            conn.commit()

        run = run_scan({}, {})

        assert run.scanned == 0
        run.classifier.get_classes.assert_not_called()

    def test_switched_off_it_does_nothing_at_all(self, test_db, run_scan):
        _add_video(test_db, "vid-1", is_tagged=1)
        path = _add_frames("vid-1", 1)[0]["frame_path"]

        run = run_scan({path: [0]}, {path: _result((A, 0.9))}, face_detection=False)

        assert run.scanned == 0
        run.detector_cls.assert_not_called()
        assert _rows(test_db, "SELECT COUNT(*) FROM faces") == [(0,)]
        assert _rows(test_db, "SELECT facesScanned FROM videos") == [(0,)]

    def test_a_video_with_no_keyframes_is_marked_rather_than_reprobed(
        self, test_db, run_scan
    ):
        # An undecodable file is tagged as empty; unmarked it would be picked
        # up by every future scan forever.
        _add_video(test_db, "vid-empty", is_tagged=1)

        run = run_scan({}, {})

        assert run.scanned == 1
        assert _rows(test_db, "SELECT facesScanned FROM videos") == [(1,)]

    def test_a_purged_cache_is_resampled_before_anything_is_classified(
        self, test_db, run_scan
    ):
        """With no JPEGs left there is nothing to classify, so every keyframe
        has to come back before a person can be found in any of them."""
        _add_video(test_db, "vid-1", is_tagged=1)
        _add_frames("vid-1", 2, purged=True)

        run = run_scan({}, {})

        first_call = run.refresh.call_args_list[0]
        assert [frame["id"] for frame in first_call.args[2]] == ["vid-1-f0", "vid-1-f1"]

    def test_rescanning_replaces_faces_instead_of_adding_more(self, test_db, run_scan):
        _add_video(test_db, "vid-1", is_tagged=1)
        path = _add_frames("vid-1", 1)[0]["frame_path"]

        for _ in range(2):
            run_scan({path: [0]}, {path: _result((A, 0.9))})
            with closing(sqlite3.connect(test_db)) as conn:
                conn.execute("UPDATE videos SET facesScanned = 0")
                conn.commit()

        assert _rows(test_db, "SELECT frame_id FROM faces") == [("vid-1-f0",)]

    def test_video_deleted_mid_scan_does_not_stop_the_rest(self, test_db, run_scan):
        _add_video(test_db, "vid-gone", is_tagged=1)
        _add_video(test_db, "vid-kept", is_tagged=1)
        gone = _add_frames("vid-gone", 1)[0]["frame_path"]
        kept = _add_frames("vid-kept", 1)[0]["frame_path"]

        def delete_gone_video(path: str) -> None:
            if path == gone:
                with closing(sqlite3.connect(test_db)) as conn:
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.execute("DELETE FROM videos WHERE id = 'vid-gone'")
                    conn.commit()

        run = run_scan(
            {gone: [0], kept: [0]},
            {gone: _result((A, 0.9)), kept: _result((B, 0.9))},
            on_detect=delete_gone_video,
        )

        assert run.scanned == 1
        assert _rows(test_db, "SELECT frame_id FROM faces") == [("vid-kept-f0",)]
