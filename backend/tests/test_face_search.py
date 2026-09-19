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
