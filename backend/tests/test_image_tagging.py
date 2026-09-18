import sqlite3
from unittest.mock import patch

from app.utils.images import image_util_classify_and_face_detect_images


def _image(image_id: str) -> dict:
    return {"id": image_id, "path": f"/photos/{image_id}.jpg"}


class TestClassifyAndFaceDetectImages:
    @patch("app.utils.images.db_update_image_tagged_status")
    @patch("app.utils.images.db_insert_image_classes_batch")
    @patch("app.utils.images.FaceDetector")
    @patch("app.utils.images.ObjectClassifier")
    def test_image_deleted_mid_pass_does_not_abort_the_rest(
        self, mock_classifier_cls, mock_detector_cls, mock_insert_classes, mock_tagged
    ):
        """Inference is slow, so a folder can be removed while its images are being
        tagged. The face insert then fails its FK; the remaining images still tag."""
        mock_classifier_cls.return_value.get_classes.return_value = [0]
        mock_detector_cls.return_value.detect_faces.side_effect = [
            sqlite3.IntegrityError("FOREIGN KEY constraint failed"),
            {"faces_skipped": 2},
        ]

        skipped = image_util_classify_and_face_detect_images(
            [_image("img-gone"), _image("img-kept")]
        )

        assert skipped == 2
        mock_tagged.assert_called_once_with("img-kept", True)
        mock_classifier_cls.return_value.close.assert_called_once()
        mock_detector_cls.return_value.close.assert_called_once()
