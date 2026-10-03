from typing import Iterator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.FaceDetector import FaceDetectionResult
from app.utils.faceSearch import perform_face_search

QUERY = np.eye(128, dtype=np.float32)[0]
SAME_PERSON = QUERY.tolist()
SOMEONE_ELSE = np.eye(128, dtype=np.float32)[1].tolist()


def _stored_face(image_id: str, embedding: list) -> dict:
    """A row shaped like get_all_face_embeddings() returns."""
    return {
        "embeddings": embedding,
        "bbox": {"x": 1, "y": 2, "width": 3, "height": 4},
        "id": image_id,
        "path": f"/photos/{image_id}.jpg",
        "folder_id": "folder-1",
        "thumbnailPath": f"/thumbs/{image_id}.jpg",
        "metadata": {},
        "isTagged": True,
        "tags": None,
    }


def _video_face(video_id: str, embedding: list) -> dict:
    """A row shaped like db_get_all_video_face_embeddings() returns."""
    return {"video_id": video_id, "embeddings": embedding}


def _video_row(video_id: str) -> dict:
    """A row shaped like db_get_videos_by_ids() returns."""
    return {
        "id": video_id,
        "path": f"/videos/{video_id}.mp4",
        "folder_id": "1",
        "thumbnailPath": None,
        "metadata": {
            "name": f"{video_id}.mp4",
            "date_created": None,
            "width": 1920,
            "height": 1080,
            "file_location": f"{video_id}.mp4",
            "file_size": 1024,
            "item_type": "video/mp4",
        },
        "isFavourite": False,
        "favouritedAt": None,
        "tags": [],
    }


@pytest.fixture
def detector() -> Iterator[MagicMock]:
    with patch("app.utils.faceSearch.FaceDetector") as detector_cls:
        yield detector_cls.return_value


class TestPerformFaceSearch:
    def test_matches_on_the_detectors_embedding(self, detector):
        detector.detect_faces.return_value = FaceDetectionResult(
            embeddings=[QUERY],
            bboxes=[{"x": 0, "y": 0, "width": 50, "height": 50}],
            confidences=[0.9],
            faces_skipped=0,
        )
        with patch(
            "app.utils.faceSearch.get_all_face_embeddings",
            return_value=[
                _stored_face("img-match", SAME_PERSON),
                _stored_face("img-other", SOMEONE_ELSE),
            ],
        ):
            response = perform_face_search("/query.jpg")

        assert response.success
        assert [image.id for image in response.data] == ["img-match"]
        detector.detect_faces.assert_called_once_with("/query.jpg")
        detector.close.assert_called_once()

    def test_finds_the_person_in_videos_and_lists_each_video_once(self, detector):
        """A person appears in many keyframes of one video; the result should
        name the video once, ranked by its best-matching face."""
        detector.detect_faces.return_value = FaceDetectionResult(
            embeddings=[QUERY],
            bboxes=[{"x": 0, "y": 0, "width": 50, "height": 50}],
            confidences=[0.9],
            faces_skipped=0,
        )
        weaker = (0.7 * QUERY + np.sqrt(1 - 0.49) * np.eye(128)[5]).tolist()
        with (
            patch("app.utils.faceSearch.get_all_face_embeddings", return_value=[]),
            patch(
                "app.utils.faceSearch.db_get_all_video_face_embeddings",
                return_value=[
                    _video_face("vid-weak", weaker),
                    _video_face("vid-strong", SAME_PERSON),
                    _video_face("vid-strong", weaker),  # same video, worse face
                    _video_face("vid-other", SOMEONE_ELSE),
                ],
            ),
            patch(
                "app.utils.faceSearch.db_get_videos_by_ids",
                side_effect=lambda ids: [_video_row(v) for v in ids],
            ),
        ):
            response = perform_face_search("/query.jpg")

        assert response.success
        assert [video.id for video in response.videos] == ["vid-strong", "vid-weak"]

    def test_video_only_library_still_searches(self, detector):
        """The early return is about having no faces at all, not no photos."""
        detector.detect_faces.return_value = FaceDetectionResult(
            embeddings=[QUERY],
            bboxes=[{"x": 0, "y": 0, "width": 50, "height": 50}],
            confidences=[0.9],
            faces_skipped=0,
        )
        with (
            patch("app.utils.faceSearch.get_all_face_embeddings", return_value=[]),
            patch(
                "app.utils.faceSearch.db_get_all_video_face_embeddings",
                return_value=[_video_face("vid-1", SAME_PERSON)],
            ),
            patch(
                "app.utils.faceSearch.db_get_videos_by_ids",
                side_effect=lambda ids: [_video_row(v) for v in ids],
            ),
        ):
            response = perform_face_search("/query.jpg")

        assert [video.id for video in response.videos] == ["vid-1"]
        assert "No face embeddings available" not in response.message

    def test_reports_when_no_face_is_found(self, detector):
        detector.detect_faces.return_value = FaceDetectionResult(
            embeddings=[], bboxes=[], confidences=[], faces_skipped=2
        )

        response = perform_face_search("/query.jpg")

        assert response.success
        assert response.data == []
        assert response.message == "No faces detected in the image."

    def test_detector_failure_is_reported_not_raised(self, detector):
        detector.detect_faces.side_effect = RuntimeError("model missing")

        response = perform_face_search("/query.jpg")

        assert not response.success
        assert "model missing" in response.message
        detector.close.assert_called_once()
