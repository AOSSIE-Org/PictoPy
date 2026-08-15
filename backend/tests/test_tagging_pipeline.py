"""
One image OpenCV cannot decode used to abort the whole AI tagging pass, so
every image queued behind it stayed untagged. These cover the skip.
"""

from unittest.mock import patch

from app.utils.images import image_util_classify_and_face_detect_images


def _image(image_id: str) -> dict:
    return {"id": image_id, "path": f"/photos/{image_id}.jpg"}


class TestClassifyAndFaceDetectImages:
    @patch("app.utils.images.db_update_image_tagged_status")
    @patch("app.utils.images.db_insert_image_classes_batch")
    @patch("app.utils.images.FaceDetector")
    @patch("app.utils.images.ObjectClassifier")
    def test_unreadable_image_skipped_and_later_images_still_tagged(
        self,
        mock_classifier_cls,
        mock_detector_cls,
        mock_insert_classes,
        mock_update_tagged,
    ):
        def get_classes(image_path):
            # img1 is the unreadable one -- cv2.imread returns None for it, so
            # the classifier returns None instead of a list of class ids.
            return None if "img1" in image_path else [17]

        mock_classifier_cls.return_value.get_classes.side_effect = get_classes

        images = [_image("img0"), _image("img1"), _image("img2")]

        image_util_classify_and_face_detect_images(images)

        tagged = [call.args[0] for call in mock_update_tagged.call_args_list]
        assert tagged == ["img0", "img2"]
        assert mock_insert_classes.call_count == 2
