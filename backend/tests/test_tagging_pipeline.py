"""
One image OpenCV cannot decode used to abort the whole AI tagging pass, so
every image queued behind it stayed untagged. These cover the skip.
"""

from unittest.mock import call, patch

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
    ) -> None:
        def get_classes(image_path):
            # img1 is the unreadable one -- cv2.imread returns None for it, so
            # the classifier returns None instead of a list of class ids.
            if "img1" in image_path:
                return None
            # class 0 is "person", which is what sends img2 to face detection.
            return [0, 17] if "img2" in image_path else [17]

        mock_classifier_cls.return_value.get_classes.side_effect = get_classes
        mock_detect_faces = mock_detector_cls.return_value.detect_faces
        mock_detect_faces.return_value = {"faces_skipped": 0}

        images = [_image("img0"), _image("img1"), _image("img2")]

        image_util_classify_and_face_detect_images(images)

        # Only the readable images are marked tagged, and the status argument
        # matters: passing False here would leave them queued forever.
        assert mock_update_tagged.call_args_list == [
            call("img0", True),
            call("img2", True),
        ]

        # Assert the pairs themselves, not just how many calls were made, so a
        # class attached to the wrong image is caught.
        assert mock_insert_classes.call_args_list == [
            call([("img0", 17)]),
            call([("img2", 0), ("img2", 17)]),
        ]

        # img1 never reaches face detection, and img2 does because it has a
        # person in it.
        assert mock_detect_faces.call_args_list == [
            call("img2", "/photos/img2.jpg")
        ]

    @patch("app.utils.images.db_update_image_tagged_status")
    @patch("app.utils.images.db_insert_image_classes_batch")
    @patch("app.utils.images.FaceDetector")
    @patch("app.utils.images.ObjectClassifier")
    def test_unreadable_image_is_logged(
        self,
        mock_classifier_cls,
        mock_detector_cls,
        mock_insert_classes,
        mock_update_tagged,
        caplog,
    ) -> None:
        mock_classifier_cls.return_value.get_classes.return_value = None

        image_util_classify_and_face_detect_images([_image("img1")])

        assert "/photos/img1.jpg" in caplog.text
        mock_update_tagged.assert_not_called()
