"""
Tests for the images API routes: GET / (get_all_images) and POST /toggle-favourite.

Uses the same style as test_albums.py: FastAPI TestClient and mocked DB/helpers.
All DB access is mocked, so to run without the session DB setup use:
  PICTOPY_SKIP_DB_SETUP=1 pytest tests/test_images.py -v
"""
import sys
import os
import pytest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes import images as images_router

app = FastAPI()
app.include_router(images_router.router, prefix="/images", tags=["images"])

client = TestClient(app)


# ##############################
# Pytest Fixtures
# ##############################


def _make_metadata():
    """Minimal metadata dict matching MetadataModel (name, date_created, width, height, etc.)."""
    return {
        "name": "photo.jpg",
        "date_created": "2024-01-15T10:00:00",
        "width": 1920,
        "height": 1080,
        "file_location": "/path/to/photo.jpg",
        "file_size": 1024000,
        "item_type": "image",
        "latitude": None,
        "longitude": None,
        "location": None,
    }


@pytest.fixture
def mock_db_image():
    """Single image as returned by db_get_all_images (with metadata as dict)."""
    return {
        "id": str(uuid.uuid4()),
        "path": "/photos/2024/photo.jpg",
        "folder_id": "42",
        "thumbnailPath": "/thumbnails/abc.jpg",
        "metadata": _make_metadata(),
        "isTagged": True,
        "isFavourite": False,
        "tags": ["person", "outdoor"],
    }


@pytest.fixture
def mock_db_image_untagged():
    """Image with isTagged False, no tags."""
    return {
        "id": str(uuid.uuid4()),
        "path": "/photos/2024/other.jpg",
        "folder_id": "42",
        "thumbnailPath": "/thumbnails/other.jpg",
        "metadata": _make_metadata(),
        "isTagged": False,
        "isFavourite": False,
        "tags": None,
    }


# ##############################
# Test Classes
# ##############################


class TestGetAllImages:
    """Test suite for GET /images/ (get_all_images)."""

    def test_get_all_images_success(self, mock_db_image):
        """GET / returns 200 and image list when db returns data."""
        with patch("app.routes.images.db_get_all_images") as mock_get:
            mock_get.return_value = [mock_db_image]

            response = client.get("/images/")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "message" in data
            assert "Successfully retrieved 1 images" in data["message"]
            assert "data" in data
            assert len(data["data"]) == 1

            img = data["data"][0]
            assert img["id"] == mock_db_image["id"]
            assert img["path"] == mock_db_image["path"]
            assert img["folder_id"] == mock_db_image["folder_id"]
            assert img["thumbnailPath"] == mock_db_image["thumbnailPath"]
            assert img["isTagged"] == mock_db_image["isTagged"]
            assert img["isFavourite"] == mock_db_image["isFavourite"]
            assert img["tags"] == mock_db_image["tags"]
            assert img["metadata"]["name"] == mock_db_image["metadata"]["name"]
            assert img["metadata"]["width"] == mock_db_image["metadata"]["width"]

            mock_get.assert_called_once_with(tagged=None)

    def test_get_all_images_empty_list(self):
        """GET / returns 200 and empty data when no images exist."""
        with patch("app.routes.images.db_get_all_images") as mock_get:
            mock_get.return_value = []

            response = client.get("/images/")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "Successfully retrieved 0 images" in data["message"]
            assert data["data"] == []

            mock_get.assert_called_once_with(tagged=None)

    @pytest.mark.parametrize("tagged_value", [True, False])
    def test_get_all_images_tagged_filter(self, mock_db_image, tagged_value):
        """GET /?tagged=<bool> passes filter to db_get_all_images."""
        with patch("app.routes.images.db_get_all_images") as mock_get:
            mock_get.return_value = [mock_db_image] if tagged_value else []

            response = client.get("/images/", params={"tagged": tagged_value})
            assert response.status_code == 200

            mock_get.assert_called_once_with(tagged=tagged_value)

    def test_get_all_images_internal_error(self):
        """GET / returns 500 when db raises."""
        with patch("app.routes.images.db_get_all_images") as mock_get:
            mock_get.side_effect = RuntimeError("DB connection failed")

            response = client.get("/images/")
            assert response.status_code == 500

            detail = response.json()["detail"]
            assert detail["success"] is False
            assert detail["error"] == "Internal server error"
            assert "Unable to retrieve images" in detail["message"]


class TestToggleFavourite:
    """Test suite for POST /images/toggle-favourite."""

    def test_toggle_favourite_success(self, mock_db_image):
        """POST /toggle-favourite returns 200 and updated isFavourite when toggle succeeds."""
        image_id = mock_db_image["id"]
        # After toggle, the route fetches all images and picks this one
        updated = {**mock_db_image, "isFavourite": True}

        with patch(
            "app.routes.images.db_toggle_image_favourite_status"
        ) as mock_toggle, patch("app.routes.images.db_get_all_images") as mock_get:
            mock_toggle.return_value = True
            mock_get.return_value = [updated]

            response = client.post(
                "/images/toggle-favourite",
                json={"image_id": image_id},
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["image_id"] == image_id
            assert data["isFavourite"] is True

            mock_toggle.assert_called_once_with(image_id)
            mock_get.assert_called_once_with()

    def test_toggle_favourite_not_found(self):
        """POST /toggle-favourite returns 404 when image not found or toggle fails."""
        image_id = str(uuid.uuid4())

        with patch(
            "app.routes.images.db_toggle_image_favourite_status"
        ) as mock_toggle:
            mock_toggle.return_value = False

            response = client.post(
                "/images/toggle-favourite",
                json={"image_id": image_id},
            )
            assert response.status_code == 404
            assert response.json()["detail"] == "Image not found or failed to toggle"

            mock_toggle.assert_called_once_with(image_id)

    def test_toggle_favourite_internal_error(self):
        """POST /toggle-favourite returns 500 when db raises."""
        image_id = str(uuid.uuid4())

        with patch(
            "app.routes.images.db_toggle_image_favourite_status"
        ) as mock_toggle:
            mock_toggle.side_effect = RuntimeError("DB error")

            response = client.post(
                "/images/toggle-favourite",
                json={"image_id": image_id},
            )
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_toggle_favourite_missing_image_id(self):
        """POST /toggle-favourite with missing image_id returns 422."""
        response = client.post(
            "/images/toggle-favourite",
            json={},
        )
        assert response.status_code == 422
