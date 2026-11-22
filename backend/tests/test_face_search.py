from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.FaceDetector import FaceDetectionResult
from app.config.settings import FACE_SEARCH_MAX_SELECTED_FACES
from app.utils.faceSearch import (
    InvalidFaceSelection,
    detect_faces_for_preview,
    perform_face_search,
)

QUERY = np.eye(128, dtype=np.float32)[0]
SAME_PERSON = QUERY.tolist()
SOMEONE_ELSE = np.eye(128, dtype=np.float32)[1].tolist()
BOX = {"x": 1, "y": 2, "width": 3, "height": 4}
BOX_RIGHT = {"x": 90, "y": 2, "width": 3, "height": 4}


def _image_face(image_id: str, embedding: list, bbox: Optional[dict] = BOX) -> dict:
    """A row shaped like db_get_all_image_face_embeddings() returns."""
    return {"image_id": image_id, "embeddings": embedding, "bbox": bbox}


def _image_row(image_id: str, tags: Optional[list] = None) -> dict:
    """A row shaped like db_get_images_by_ids() returns (metadata is raw JSON)."""
    return {
        "id": image_id,
        "path": f"/photos/{image_id}.jpg",
        "folder_id": "folder-1",
        "thumbnailPath": f"/thumbs/{image_id}.jpg",
        "metadata": "{}",
        "isTagged": True,
        "tags": tags,
    }


def _images_by_ids(ids: list) -> list:
    return [_image_row(i) for i in ids]


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
            image_width=640,
            image_height=480,
        )
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings",
                return_value=[
                    _image_face("img-match", SAME_PERSON),
                    _image_face("img-other", SOMEONE_ELSE),
                ],
            ),
            patch(
                "app.utils.faceSearch.db_get_images_by_ids",
                side_effect=_images_by_ids,
            ),
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
            image_width=640,
            image_height=480,
        )
        weaker = (0.7 * QUERY + np.sqrt(1 - 0.49) * np.eye(128)[5]).tolist()
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings", return_value=[]
            ),
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
            image_width=640,
            image_height=480,
        )
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings", return_value=[]
            ),
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
            embeddings=[],
            bboxes=[],
            confidences=[],
            faces_skipped=2,
            image_width=640,
            image_height=480,
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


class TestMultiFacePhotos:
    @staticmethod
    def _search(detector, image_faces, rows=_images_by_ids):
        detector.detect_faces.return_value = FaceDetectionResult(
            embeddings=[QUERY],
            bboxes=[BOX],
            confidences=[0.9],
            faces_skipped=0,
            image_width=640,
            image_height=480,
        )
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings",
                return_value=image_faces,
            ),
            patch(
                "app.utils.faceSearch.db_get_all_video_face_embeddings", return_value=[]
            ),
            patch("app.utils.faceSearch.db_get_images_by_ids", side_effect=rows),
        ):
            return perform_face_search("/query.jpg")

    def test_finds_a_person_who_is_not_the_first_face(self, detector):
        response = self._search(
            detector,
            [
                _image_face("group", SOMEONE_ELSE, BOX),
                _image_face("group", SAME_PERSON, BOX_RIGHT),
            ],
        )

        assert [image.id for image in response.data] == ["group"]

    def test_group_photo_is_listed_once_framed_on_the_matching_face(self, detector):
        response = self._search(
            detector,
            [
                _image_face("group", SAME_PERSON, BOX),
                _image_face("group", _looks_like(0.7), BOX_RIGHT),
                _image_face("group", SOMEONE_ELSE, BOX_RIGHT),
            ],
        )

        assert len(response.data) == 1
        assert response.data[0].bboxes.x == BOX["x"]

    def test_images_rank_by_their_best_face(self, detector):
        response = self._search(
            detector,
            [
                _image_face("weak", _looks_like(0.7)),
                _image_face("strong", SOMEONE_ELSE),
                _image_face("strong", SAME_PERSON),
            ],
        )

        assert [image.id for image in response.data] == ["strong", "weak"]

    def test_tags_come_back_once_each(self, detector):
        response = self._search(
            detector,
            [_image_face("group", SAME_PERSON), _image_face("group", SAME_PERSON)],
            rows=lambda ids: [_image_row(i, ["dog", "tree"]) for i in ids],
        )

        assert response.data[0].tags == ["dog", "tree"]

    def test_face_without_a_box_still_matches(self, detector):
        response = self._search(detector, [_image_face("old", SAME_PERSON, None)])

        assert [image.id for image in response.data] == ["old"]
        assert response.data[0].bboxes is None

    def test_image_deleted_before_loading_is_skipped(self, detector):
        response = self._search(
            detector, [_image_face("gone", SAME_PERSON)], rows=lambda ids: []
        )

        assert response.success
        assert response.data == []


THIRD_PERSON = np.eye(128, dtype=np.float32)[2].tolist()


def _near(axis: int, similarity: float) -> list:
    """An embedding at the given cosine similarity to person `axis`."""
    spill = 127
    vector = np.zeros(128, dtype=np.float32)
    vector[axis] = similarity
    vector[spill] = np.sqrt(1 - similarity**2)
    return vector.tolist()


def _detected(*embeddings: list, skipped: int = 0) -> FaceDetectionResult:
    """A detector result holding one face per embedding, boxed left to right."""
    return FaceDetectionResult(
        embeddings=[np.array(embedding, dtype=np.float32) for embedding in embeddings],
        bboxes=[
            {"x": i * 100, "y": 0, "width": 50, "height": 50}
            for i in range(len(embeddings))
        ],
        confidences=[0.9 - i * 0.1 for i in range(len(embeddings))],
        faces_skipped=skipped,
        image_width=640,
        image_height=480,
    )


class TestSelectedFaces:
    @staticmethod
    def _search(
        detector,
        detected,
        image_faces=(),
        video_faces=(),
        face_indices=None,
        match_mode="match_any",
    ):
        detector.detect_faces.return_value = detected
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings",
                return_value=list(image_faces),
            ),
            patch(
                "app.utils.faceSearch.db_get_all_video_face_embeddings",
                return_value=list(video_faces),
            ),
            patch(
                "app.utils.faceSearch.db_get_images_by_ids",
                side_effect=_images_by_ids,
            ),
            patch(
                "app.utils.faceSearch.db_get_videos_by_ids",
                side_effect=lambda ids: [_video_row(v) for v in ids],
            ),
        ):
            return perform_face_search("/query.jpg", face_indices, match_mode)

    def test_defaults_to_the_first_face(self, detector):
        response = self._search(
            detector,
            _detected(SOMEONE_ELSE, SAME_PERSON),
            [_image_face("first", SOMEONE_ELSE), _image_face("second", SAME_PERSON)],
        )

        assert [image.id for image in response.data] == ["first"]

    def test_searches_with_the_selected_face(self, detector):
        response = self._search(
            detector,
            _detected(SOMEONE_ELSE, SAME_PERSON),
            [_image_face("first", SOMEONE_ELSE), _image_face("second", SAME_PERSON)],
            face_indices=[1],
        )

        assert [image.id for image in response.data] == ["second"]

    def test_match_any_returns_photos_of_either_selected_face(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE, THIRD_PERSON),
            [
                _image_face("a", SAME_PERSON),
                _image_face("b", SOMEONE_ELSE),
                _image_face("c", THIRD_PERSON),
            ],
            face_indices=[0, 1],
        )

        assert sorted(image.id for image in response.data) == ["a", "b"]

    def test_match_count_is_how_many_selected_faces_the_photo_holds(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            [
                _image_face("both", SAME_PERSON),
                _image_face("both", SOMEONE_ELSE),
                _image_face("one", SAME_PERSON),
            ],
            face_indices=[0, 1],
        )

        counts = {image.id: image.match_count for image in response.data}
        assert counts == {"both": 2, "one": 1}

    def test_match_all_needs_every_selected_face_in_the_photo(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            [
                _image_face("both", SAME_PERSON),
                _image_face("both", SOMEONE_ELSE),
                _image_face("only-first", SAME_PERSON),
                _image_face("only-second", SOMEONE_ELSE),
            ],
            face_indices=[0, 1],
            match_mode="match_all",
        )

        assert [image.id for image in response.data] == ["both"]
        assert response.data[0].match_count == 2

    def test_match_all_with_one_face_is_the_same_as_match_any(self, detector):
        stored = [_image_face("a", SAME_PERSON), _image_face("b", SOMEONE_ELSE)]
        detected = _detected(SAME_PERSON, SOMEONE_ELSE)

        any_ids = self._search(detector, detected, stored, face_indices=[0])
        all_ids = self._search(
            detector, detected, stored, face_indices=[0], match_mode="match_all"
        )

        assert [i.id for i in all_ids.data] == [i.id for i in any_ids.data] == ["a"]

    def test_match_all_does_not_let_one_stored_face_answer_two_selected_faces(
        self, detector
    ):
        """Two lookalike selections need two stored faces, not one counted twice."""
        detected = _detected(SAME_PERSON, _near(0, 0.9))
        stored = [
            _image_face("one-face", SAME_PERSON),
            _image_face("two-faces", SAME_PERSON),
            _image_face("two-faces", _near(0, 0.9)),
        ]

        response = self._search(
            detector,
            detected,
            stored,
            face_indices=[0, 1],
            match_mode="match_all",
        )

        assert [image.id for image in response.data] == ["two-faces"]

    def test_match_all_ranks_by_the_mean_similarity_of_the_matches(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            [
                _image_face("weak", SAME_PERSON),
                _image_face("weak", _near(1, 0.7)),
                _image_face("strong", SAME_PERSON),
                _image_face("strong", SOMEONE_ELSE),
            ],
            face_indices=[0, 1],
            match_mode="match_all",
        )

        assert [image.id for image in response.data] == ["strong", "weak"]

    def test_match_all_frames_the_best_matching_face(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            [
                _image_face("group", _near(1, 0.8), BOX_RIGHT),
                _image_face("group", SAME_PERSON, BOX),
            ],
            face_indices=[0, 1],
            match_mode="match_all",
        )

        assert response.data[0].bboxes.x == BOX["x"]

    def test_duplicate_indices_count_once(self, detector):
        """[0, 0] under match_all must not demand two stored faces."""
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            [_image_face("a", SAME_PERSON)],
            face_indices=[0, 0],
            match_mode="match_all",
        )

        assert [image.id for image in response.data] == ["a"]

    @pytest.mark.parametrize("bad_index", [2, 99, -1])
    def test_an_index_outside_the_detected_faces_is_rejected(self, detector, bad_index):
        with pytest.raises(InvalidFaceSelection, match="between 0 and 1"):
            self._search(
                detector,
                _detected(SAME_PERSON, SOMEONE_ELSE),
                [_image_face("a", SAME_PERSON)],
                face_indices=[0, bad_index],
            )

        detector.close.assert_called_once()

    def test_selecting_more_faces_than_the_cap_is_rejected(self, detector):
        crowd = _detected(*[SAME_PERSON] * (FACE_SEARCH_MAX_SELECTED_FACES + 1))

        with pytest.raises(InvalidFaceSelection, match="at most"):
            self._search(
                detector,
                crowd,
                [_image_face("a", SAME_PERSON)],
                face_indices=list(range(FACE_SEARCH_MAX_SELECTED_FACES + 1)),
            )

        detector.close.assert_called_once()

    def test_the_cap_counts_distinct_faces_and_allows_exactly_the_cap(self, detector):
        crowd = _detected(*[SAME_PERSON] * (FACE_SEARCH_MAX_SELECTED_FACES + 1))
        stored = [_image_face("a", SAME_PERSON)]

        at_the_cap = self._search(
            detector,
            crowd,
            stored,
            face_indices=list(range(FACE_SEARCH_MAX_SELECTED_FACES)),
        )
        repeated = self._search(
            detector,
            crowd,
            stored,
            face_indices=[0] * (FACE_SEARCH_MAX_SELECTED_FACES + 3),
        )

        assert [image.id for image in at_the_cap.data] == ["a"]
        assert [image.id for image in repeated.data] == ["a"]

    def test_a_photo_without_faces_reports_it_whatever_was_selected(self, detector):
        response = self._search(detector, _detected(), face_indices=[3])

        assert response.success
        assert response.message == "No faces detected in the image."

    def test_match_all_finds_videos_holding_every_selected_face(self, detector):
        response = self._search(
            detector,
            _detected(SAME_PERSON, SOMEONE_ELSE),
            video_faces=[
                _video_face("vid-both", SAME_PERSON),
                _video_face("vid-both", SOMEONE_ELSE),
                _video_face("vid-one", SAME_PERSON),
            ],
            face_indices=[0, 1],
            match_mode="match_all",
        )

        assert [video.id for video in response.videos] == ["vid-both"]


class TestDetectFacesForPreview:
    def test_lists_each_face_with_its_index_box_and_confidence(self, detector):
        detector.detect_faces.return_value = _detected(
            SAME_PERSON, SOMEONE_ELSE, skipped=1
        )

        response = detect_faces_for_preview("/query.jpg")

        assert response.success
        assert response.message == "Detected 2 faces."
        data = response.data
        assert data is not None
        assert (data.image_width, data.image_height, data.faces_skipped) == (
            640,
            480,
            1,
        )
        assert [face.index for face in data.faces] == [0, 1]
        assert data.faces[1].bbox.x == 100
        assert data.faces[0].confidence == pytest.approx(0.9)
        detector.close.assert_called_once()

    def test_one_face_reads_in_the_singular(self, detector):
        detector.detect_faces.return_value = _detected(SAME_PERSON)

        assert detect_faces_for_preview("/query.jpg").message == "Detected 1 face."

    def test_reports_when_no_face_is_found(self, detector):
        detector.detect_faces.return_value = _detected(skipped=2)

        response = detect_faces_for_preview("/query.jpg")

        assert response.success
        assert response.message == "No faces detected in the image."
        assert response.data is not None
        assert response.data.faces == []
        assert response.data.faces_skipped == 2

    def test_an_unreadable_image_has_no_data(self, detector):
        detector.detect_faces.return_value = None

        response = detect_faces_for_preview("/query.jpg")

        assert response.success
        assert response.data is None

    def test_detector_failure_is_reported_not_raised(self, detector):
        detector.detect_faces.side_effect = RuntimeError("model missing")

        response = detect_faces_for_preview("/query.jpg")

        assert not response.success
        assert "model missing" in response.message
        detector.close.assert_called_once()

    def test_indices_match_the_ones_the_search_accepts(self, detector):
        """The preview's index n must be the face the search uses for index n."""
        detected = _detected(SOMEONE_ELSE, SAME_PERSON)
        detector.detect_faces.return_value = detected
        with (
            patch(
                "app.utils.faceSearch.db_get_all_image_face_embeddings",
                return_value=[_image_face("target", SAME_PERSON)],
            ),
            patch(
                "app.utils.faceSearch.db_get_all_video_face_embeddings",
                return_value=[],
            ),
            patch(
                "app.utils.faceSearch.db_get_images_by_ids",
                side_effect=_images_by_ids,
            ),
        ):
            preview = detect_faces_for_preview("/query.jpg")
            assert preview.data is not None
            search = perform_face_search("/query.jpg", [preview.data.faces[1].index])

        assert [image.id for image in search.data] == ["target"]


def _looks_like(similarity: float) -> list:
    """An embedding at the given cosine similarity to QUERY."""
    return (similarity * QUERY + np.sqrt(1 - similarity**2) * np.eye(128)[5]).tolist()
