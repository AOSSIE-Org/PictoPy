import sqlite3
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import call, patch

import numpy as np
import pytest

from app.database.images import UntaggedImageRecord
from app.models.FaceDetector import FaceDetectionResult
from app.utils.images import image_util_classify_and_face_detect_images


def _image(image_id: str) -> UntaggedImageRecord:
    return {
        "id": image_id,
        "path": f"/photos/{image_id}.jpg",
        "folder_id": "folder-1",
        "thumbnailPath": f"/thumbnails/{image_id}.jpg",
        "metadata": {},
    }


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
        patch("app.utils.images.db_insert_image_classes_batch") as insert_classes,
        patch("app.utils.images.db_insert_face_embeddings_by_image_id") as insert,
        patch("app.utils.images.db_update_image_tagged_status") as mark_tagged,
    ):
        yield SimpleNamespace(
            classifier_cls=classifier_cls,
            detector_cls=detector_cls,
            classifier=classifier_cls.return_value,
            detector=detector_cls.return_value,
            insert_classes=insert_classes,
            insert_faces=insert,
            mark_tagged=mark_tagged,
        )


class TestClassifyAndFaceDetectImages:
    def test_persists_detected_faces_against_the_image(
        self, pipeline: SimpleNamespace
    ) -> None:
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

    def test_no_insert_when_every_face_fails_the_gate(
        self, pipeline: SimpleNamespace
    ) -> None:
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.return_value = _faces(0, skipped=3)

        skipped = image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)
        assert skipped == 3

    def test_no_face_detection_without_a_person(
        self, pipeline: SimpleNamespace
    ) -> None:
        pipeline.classifier.get_classes.return_value = [2]  # car

        image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.detector.detect_faces.assert_not_called()
        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)

    def test_face_detector_none_is_still_marked_tagged(
        self, pipeline: SimpleNamespace
    ) -> None:
        """Preserve the existing policy for a detector that cannot read the file."""
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.return_value = None

        skipped = image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-1", True)
        assert skipped == 0

    def test_image_deleted_mid_pass_does_not_abort_the_rest(
        self, pipeline: SimpleNamespace
    ) -> None:
        """A folder can be removed during inference, making the face insert fail."""
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

    @pytest.mark.parametrize("failure", ["unreadable", "classifier", "detector"])
    def test_bad_image_does_not_block_healthy_images(
        self,
        pipeline: SimpleNamespace,
        caplog: pytest.LogCaptureFixture,
        failure: str,
    ) -> None:
        before = _faces(1, skipped=2)
        after = _faces(1, skipped=3)
        pipeline.classifier.get_classes.return_value = [0]
        if failure == "detector":
            pipeline.detector.detect_faces.side_effect = [
                before,
                RuntimeError("inference failed"),
                after,
            ]
        else:
            bad_result = (
                None if failure == "unreadable" else RuntimeError("inference failed")
            )
            pipeline.classifier.get_classes.side_effect = [[0], bad_result, [0]]
            pipeline.detector.detect_faces.side_effect = [before, after]

        skipped = image_util_classify_and_face_detect_images(
            [_image("img-before"), _image("img-bad"), _image("img-after")]
        )

        assert skipped == 5
        assert pipeline.classifier.get_classes.call_args_list == [
            call("/photos/img-before.jpg"),
            call("/photos/img-bad.jpg"),
            call("/photos/img-after.jpg"),
        ]
        assert pipeline.mark_tagged.call_args_list == [
            call("img-before", True),
            call("img-after", True),
        ]
        assert [entry.args[0] for entry in pipeline.insert_faces.call_args_list] == [
            "img-before",
            "img-after",
        ]
        expected_class_writes = [call([("img-before", 0)])]
        expected_detector_calls = [call("/photos/img-before.jpg")]
        if failure == "detector":
            expected_class_writes.append(call([("img-bad", 0)]))
            expected_detector_calls.append(call("/photos/img-bad.jpg"))
        expected_class_writes.append(call([("img-after", 0)]))
        expected_detector_calls.append(call("/photos/img-after.jpg"))
        assert pipeline.insert_classes.call_args_list == expected_class_writes
        assert pipeline.detector.detect_faces.call_args_list == expected_detector_calls
        pipeline.classifier.close.assert_called_once()
        pipeline.detector.close.assert_called_once()
        failures = [
            record for record in caplog.records if "img-bad" in record.getMessage()
        ]
        assert len(failures) == 1
        assert "/photos/img-bad.jpg" in failures[0].getMessage()
        if failure == "unreadable":
            assert failures[0].exc_info is None
        else:
            assert failures[0].exc_info is not None
            assert isinstance(failures[0].exc_info[1], RuntimeError)
            assert "inference failed" in caplog.text

    def test_empty_classes_is_successfully_tagged(
        self, pipeline: SimpleNamespace
    ) -> None:
        pipeline.classifier.get_classes.return_value = []

        skipped = image_util_classify_and_face_detect_images([_image("img-empty")])

        assert skipped == 0
        pipeline.insert_classes.assert_not_called()
        pipeline.detector.detect_faces.assert_not_called()
        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_called_once_with("img-empty", True)
        pipeline.classifier.close.assert_called_once()
        pipeline.detector.close.assert_called_once()

    @pytest.mark.parametrize("failure", ["unreadable", "classifier", "detector"])
    def test_failed_image_can_be_retried_successfully(
        self, pipeline: SimpleNamespace, failure: str
    ) -> None:
        pipeline.classifier.get_classes.return_value = [0]
        if failure == "detector":
            pipeline.detector.detect_faces.side_effect = [
                RuntimeError("inference failed"),
                _faces(1, skipped=2),
            ]
        else:
            bad_result = (
                None if failure == "unreadable" else RuntimeError("inference failed")
            )
            pipeline.classifier.get_classes.side_effect = [bad_result, [0]]
            pipeline.detector.detect_faces.return_value = _faces(1, skipped=2)
        images = [_image("img-retry")]

        assert image_util_classify_and_face_detect_images(images) == 0
        pipeline.mark_tagged.assert_not_called()
        pipeline.insert_faces.assert_not_called()

        assert image_util_classify_and_face_detect_images(images) == 2
        pipeline.mark_tagged.assert_called_once_with("img-retry", True)
        pipeline.insert_faces.assert_called_once()
        assert pipeline.insert_faces.call_args.args[0] == "img-retry"
        assert pipeline.classifier.close.call_count == 2
        assert pipeline.detector.close.call_count == 2

    @pytest.mark.parametrize("write", ["insert_classes", "insert_faces", "mark_tagged"])
    def test_database_errors_still_propagate(
        self, pipeline: SimpleNamespace, write: str
    ) -> None:
        pipeline.classifier.get_classes.return_value = [0]
        pipeline.detector.detect_faces.return_value = _faces(1)
        getattr(pipeline, write).side_effect = sqlite3.OperationalError(
            "database locked"
        )

        with pytest.raises(sqlite3.OperationalError, match="database locked"):
            image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.classifier.close.assert_called_once()
        pipeline.detector.close.assert_called_once()

    @pytest.mark.parametrize("model", ["classifier_cls", "detector_cls"])
    def test_model_initialization_errors_still_propagate(
        self, pipeline: SimpleNamespace, model: str
    ) -> None:
        getattr(pipeline, model).side_effect = RuntimeError("model unavailable")

        with pytest.raises(RuntimeError, match="model unavailable"):
            image_util_classify_and_face_detect_images([_image("img-1")])

        pipeline.insert_classes.assert_not_called()
        pipeline.insert_faces.assert_not_called()
        pipeline.mark_tagged.assert_not_called()
