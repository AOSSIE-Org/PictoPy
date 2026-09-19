from types import SimpleNamespace
from typing import Iterator
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from app.models.FaceDetector import FaceDetector

# (x1, y1, x2, y2): two faces that clear the 1000px^2 gate around one that doesn't
FACE_A = [10, 10, 70, 70]
TOO_SMALL = [185, 185, 195, 195]
FACE_B = [100, 100, 180, 180]


@pytest.fixture
def photo(tmp_path) -> str:
    """Random noise, so every crop is sharp enough for the blur check."""
    path = tmp_path / "photo.png"
    rng = np.random.default_rng(0)
    cv2.imwrite(str(path), rng.integers(0, 256, (200, 200, 3), dtype=np.uint8))
    return str(path)


@pytest.fixture
def models() -> Iterator[SimpleNamespace]:
    """FaceDetector with its ONNX models mocked; the model files are not in CI."""
    with (
        patch("app.models.FaceDetector.YOLO_util_get_model_path", return_value="f"),
        patch("app.models.FaceDetector.YOLO") as yolo_cls,
        patch("app.models.FaceDetector.FaceNet") as facenet_cls,
    ):
        yolo = yolo_cls.return_value
        yolo.conf_threshold = 0.45
        yolo.return_value = (
            np.array([FACE_A, TOO_SMALL, FACE_B], dtype=float),
            np.array([0.9, 0.95, 0.7]),
            np.zeros(3, dtype=int),
        )
        facenet = facenet_cls.return_value
        facenet.get_embedding.side_effect = [np.full(128, 1.0), np.full(128, 2.0)]

        detector = FaceDetector()
        yield SimpleNamespace(detector=detector, facenet=facenet)
        detector.close()


class TestDetectFaces:
    def test_returns_aligned_faces_that_pass_the_gate(self, models, photo):
        result = models.detector.detect_faces(photo)

        assert result["bboxes"] == [
            {"x": 10, "y": 10, "width": 60, "height": 60},
            {"x": 100, "y": 100, "width": 80, "height": 80},
        ]
        assert result["confidences"] == [0.9, 0.7]
        assert [e[0] for e in result["embeddings"]] == [1.0, 2.0]
        assert result["faces_skipped"] == 1

    def test_rejected_faces_are_never_embedded(self, models, photo):
        models.detector.detect_faces(photo)
        assert models.facenet.get_embedding.call_count == 2

    def test_does_not_touch_the_database(self, models, photo):
        """Pure inference: persisting is the caller's job, which is what lets
        face search and video keyframes reuse this path."""
        with patch("sqlite3.connect", side_effect=AssertionError("database hit")):
            result = models.detector.detect_faces(photo)
        assert len(result["embeddings"]) == 2

    def test_unreadable_file_returns_none(self, models, tmp_path):
        assert models.detector.detect_faces(str(tmp_path / "missing.jpg")) is None
