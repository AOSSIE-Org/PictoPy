import sqlite3
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import patch

import numpy as np
import pytest

from app.models.FaceDetector import FaceDetectionResult
from app.utils.images import image_util_classify_and_face_detect_images


def _image(image_id: str) -> dict:
    return {"id": image_id, "path": f"/photos/{image_id}.jpg"}


def _faces(count: int, skipped: int = 0) -> FaceDetectionResult:
    """A detector result holding `count` embedded faces."""
    return FaceDetectionResult(
        embeddings=[np.full(128, i, dtype=np.float32) for i in range(count)],
        bboxes=[{"x": i, "y": i, "width": 40, "height": 40} for i in range(count)],
        confidences=[0.9] * count,
        faces_skipped=skipped,
    )


@pytest.fixture
def pipeline() -> Iterator[SimpleNamespace]:
    """Every model and database call the tagging loop makes, mocked."""
    with (
        patch("app.utils.images.ObjectClassifier") as classifier_cls,
        patch("app.utils.images.FaceDetector") as detector_cls,
        patch("app.utils.images.db_insert_image_classes_batch"),
        patch("app.utils.images.db_insert_face_embeddings_by_image_id") as insert,
        patch("app.utils.images.db_update_image_tagged_status") as mark_tagged,
    ):
        yield SimpleNamespace(
            classifier=classifier_cls.return_value,
            detector=detector_cls.return_value,
            insert_faces=insert,
            mark_tagged=mark_tagged,
        )


class TestClassifyAndFaceDetectImages:
    def test_persists_detected_faces_against_the_image(self, pipeline):
        pipeline.classifier.get_classes.return_value = [0]
        result = _faces(2, skipped=1)
        pipeline.detector.detect_faces.return_value = result

        skipped = image_util_classify_and_face_detect_images([_image("img-1")])

        # The detector only sees a path: it has no notion of which record it serves.
        pipeline.detector.detect_faces.assert_called_once_with("/photos/img-1.jpg")
        pipeline.insert_faces.assert_called_once_with(
            "img-1",
            result["embeddings"],
            confidence=result["confidences"],
            bbox=result["bboxes"],
        )
        pipeline.mark_tagged.assert_called_once_with("img-1", True)
        assert skipped == 1

    def test_no_insert_when_every_face_fails_the_gate(self, pipeline):
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.return_value = _faces(0, skipped=3)

        skipped = image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)
        assert skipped == 3

    def test_no_face_detection_without_a_person(self, pipeline):
        pipeline.classifier.get_classes.return_value = [2]  # car

        image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.detector.detect_faces.assert_not_called()
        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)

    def test_unreadable_image_is_still_marked_tagged(self, pipeline):
        """Otherwise every pass would retry it forever."""
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.return_value = None

        skipped = image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)
        assert skipped == 0

    def test_image_deleted_mid_pass_does_not_abort_the_rest(self, pipeline):
        """Inference is slow, so a folder can be removed while its images are being
        tagged. The face insert then fails its FK; the remaining images still tag."""
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.side_effect = [
            _faces(1, skipped=5),
            _faces(1, skipped=2),
        ]
        pipeline.insert_faces.side_effect = [
            sqlite3.IntegrityError("FOREIGN KEY constraint failed"),
            None,
        ]

        skipped = image_util_classify_and_face_detect_images(
            [_image("img-gone"), _image("img-kept")]
        )

        assert skipped == 2
        pipeline.mark_tagged.assert_called_once_with("img-kept", True)
        pipeline.classifier.close.assert_called_once()
        pipeline.detector.close.assert_called_once()
