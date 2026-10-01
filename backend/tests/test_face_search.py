import json
from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.FaceDetector import FaceDetectionResult
from app.utils.faceSearch import perform_face_search

QUERY: np.ndarray = np.eye(128, dtype=np.float32)[0]
SAME_PERSON = QUERY.tolist()
SOMEONE_ELSE = np.eye(128, dtype=np.float32)[1].tolist()

BOX_LEFT = {"x": 1, "y": 2, "width": 3, "height": 4}
BOX_RIGHT = {"x": 90, "y": 2, "width": 3, "height": 4}


def _looks_like(embedding: list, similarity: float, axis: int) -> list:
    """An embedding a given cosine distance away from `embedding`."""
    other: np.ndarray = np.eye(128, dtype=np.float32)[axis]
    return (
        similarity * np.asarray(embedding, dtype=np.float32)
        + np.sqrt(1 - similarity**2) * other
    ).tolist()


def _image_face(
    image_id: str, embedding: list, bbox: Optional[dict] = BOX_LEFT
) -> dict:
    """A row shaped like db_get_all_image_face_embeddings() returns."""
    return {"image_id": image_id, "embeddings": embedding, "bbox": bbox}


def _image_row(image_id: str, tags: Optional[list] = None) -> dict:
    """A row shaped like db_get_images_by_ids() returns.

    metadata arrives as the raw JSON string from the column, which is what the
    caller has to parse.
    """
    return {
        "id": image_id,
        "path": f"/photos/{image_id}.jpg",
        "folder_id": "folder-1",
        "thumbnailPath": f"/thumbs/{image_id}.jpg",
        "metadata": json.dumps({"name": f"{image_id}.jpg"}),
        "isTagged": True,
        "isFavourite": False,
        "favouritedAt": None,
        "latitude": None,
        "longitude": None,
        "captured_at": None,
        "tags": tags,
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
        detector_cls.return_value.detect_faces.return_value = FaceDetectionResult(
            embeddings=[QUERY],
            bboxes=[{"x": 0, "y": 0, "width": 50, "height": 50}],
            confidences=[0.9],
            faces_skipped=0,
        )
        yield detector_cls.return_value


def _search(faces: list, rows=None, videos: Optional[list] = None):
    """Run a search over the given stored faces, stubbing both hydrations."""
    if rows is None:

        def rows(ids):
            return [_image_row(i) for i in ids]

    with (
        patch(
            "app.utils.faceSearch.db_get_all_image_face_embeddings",
            return_value=faces,
        ),
        patch("app.utils.faceSearch.db_get_images_by_ids", side_effect=rows),
        patch(
            "app.utils.faceSearch.db_get_all_video_face_embeddings",
            return_value=videos or [],
        ),
        patch(
            "app.utils.faceSearch.db_get_videos_by_ids",
            side_effect=lambda ids: [_video_row(v) for v in ids],
        ),
    ):
        return perform_face_search("/query.jpg")


class TestPerformFaceSearch:
    def test_matches_on_the_detectors_embedding(self, detector):
        response = _search(
            [
                _image_face("img-match", SAME_PERSON),
                _image_face("img-other", SOMEONE_ELSE),
            ]
        )

        assert response.success
        assert [image.id for image in response.data] == ["img-match"]
        detector.detect_faces.assert_called_once_with("/query.jpg")
        detector.close.assert_called_once()

    def test_finds_a_person_who_is_not_the_first_face_in_the_photo(self, detector):
        """The whole point: a group photo stores several faces, and the one
        being searched for may be any of them."""
        response = _search(
            [
                _image_face("img-group", SOMEONE_ELSE, BOX_LEFT),
                _image_face("img-group", SAME_PERSON, BOX_RIGHT),
            ]
        )

        assert [image.id for image in response.data] == ["img-group"]

    def test_lists_a_group_photo_once_and_frames_the_matching_face(self, detector):
        """Two stored faces, one image. It appears once, boxed on the face that
        actually matched rather than whichever row came back first."""
        response = _search(
            [
                _image_face("img-group", _looks_like(SAME_PERSON, 0.7, 5), BOX_LEFT),
                _image_face("img-group", SAME_PERSON, BOX_RIGHT),
            ]
        )

        assert len(response.data) == 1
        assert response.data[0].bboxes.x == BOX_RIGHT["x"]

    def test_a_tag_is_not_repeated_once_per_stored_face(self, detector):
        response = _search(
            [
                _image_face("img-group", SAME_PERSON),
                _image_face("img-group", SAME_PERSON),
                _image_face("img-group", SAME_PERSON),
            ],
            rows=lambda ids: [_image_row(i, tags=["person", "cake"]) for i in ids],
        )

        assert response.data[0].tags == ["person", "cake"]

    def test_images_are_ranked_best_match_first(self, detector):
        response = _search(
            [
                _image_face("img-weak", _looks_like(SAME_PERSON, 0.7, 5)),
                _image_face("img-strong", SAME_PERSON),
            ]
        )

        assert [image.id for image in response.data] == ["img-strong", "img-weak"]

    def test_a_face_stored_without_a_box_still_matches(self, detector):
        """Older rows can have a null bbox. That is not a reason to lose the
        match, or to fail the whole search."""
        response = _search([_image_face("img-match", SAME_PERSON, bbox=None)])

        assert [image.id for image in response.data] == ["img-match"]
        assert response.data[0].bboxes is None

    def test_an_image_deleted_mid_search_is_dropped(self, detector):
        """Hydration is a second query, so a matched image can be gone by then."""
        response = _search([_image_face("img-gone", SAME_PERSON)], rows=lambda ids: [])

        assert response.success
        assert response.data == []

    def test_finds_the_person_in_videos_and_lists_each_video_once(self, detector):
        """A person appears in many keyframes of one video; the result should
        name the video once, ranked by its best-matching face."""
        weaker = _looks_like(SAME_PERSON, 0.7, 5)
        response = _search(
            [],
            videos=[
                _video_face("vid-weak", weaker),
                _video_face("vid-strong", SAME_PERSON),
                _video_face("vid-strong", weaker),  # same video, worse face
                _video_face("vid-other", SOMEONE_ELSE),
            ],
        )

        assert response.success
        assert [video.id for video in response.videos] == ["vid-strong", "vid-weak"]

    def test_video_only_library_still_searches(self, detector):
        """The early return is about having no faces at all, not no photos."""
        response = _search([], videos=[_video_face("vid-1", SAME_PERSON)])

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
