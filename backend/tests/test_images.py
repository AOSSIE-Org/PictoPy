"""
Test suite for the Images API endpoints.

Tests cover:
- GET /images/ - Get all images
- POST /images/toggle-favourite - Toggle favourite status
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import tempfile
import os

from app.routes.images import router as images_router


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    db_fd, db_path = tempfile.mkstemp()

    import app.config.settings

    original_db_path = app.config.settings.DATABASE_PATH
    app.config.settings.DATABASE_PATH = db_path

    yield db_path

    app.config.settings.DATABASE_PATH = original_db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def app_with_state(test_db):
    """Create FastAPI app instance for testing."""
    app = FastAPI()
    app.include_router(images_router, prefix="/images")
    return app


@pytest.fixture
def client(app_with_state):
    """Create test client."""
    return TestClient(app_with_state)


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    return {
        "id": "test-image-id-123",
        "path": "/test/path/to/image.jpg",
        "folder_id": "folder-123",
        "thumbnailPath": "/test/path/to/thumbnail.jpg",
        "metadata": {
            "name": "image.jpg",
            "date_created": "2024-01-01T12:00:00",
            "width": 1920,
            "height": 1080,
            "file_location": "/test/path/to/image.jpg",
            "file_size": 1024000,
            "item_type": "image/jpeg",
        },
        "isTagged": True,
        "isFavourite": False,
        "tags": ["person", "car"],
    }


@pytest.fixture
def sample_images_list(sample_image_data):
    """Sample list of images for testing."""
    return [
        sample_image_data,
        {
            "id": "test-image-id-456",
            "path": "/test/path/to/image2.png",
            "folder_id": "folder-456",
            "thumbnailPath": "/test/path/to/thumbnail2.jpg",
            "metadata": {
                "name": "image2.png",
                "date_created": "2024-02-15T10:30:00",
                "width": 800,
                "height": 600,
                "file_location": "/test/path/to/image2.png",
                "file_size": 512000,
                "item_type": "image/png",
            },
            "isTagged": False,
            "isFavourite": True,
            "tags": None,
        },
    ]


# ##############################
# Test Classes
# ##############################


class TestImagesAPI:
    """Test class for Images API endpoints."""

    # ============================================================================
    # GET /images/ - Get All Images Tests
    # ============================================================================

    @patch("app.routes.images.db_get_all_images")
    def test_get_all_images_success(
        self, mock_get_all_images, client, sample_images_list
    ):
        """Test successfully retrieving all images."""
        mock_get_all_images.return_value = sample_images_list

        response = client.get("/images/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 2 images" in data["message"]
        assert len(data["data"]) == 2

        # Check first image details
        first_image = data["data"][0]
        assert first_image["id"] == "test-image-id-123"
        assert first_image["path"] == "/test/path/to/image.jpg"
        assert first_image["isTagged"] is True
        assert first_image["tags"] == ["person", "car"]

        mock_get_all_images.assert_called_once_with(tagged=None)

    @patch("app.routes.images.db_get_all_images")
    def test_get_all_images_empty(self, mock_get_all_images, client):
        """Test retrieving all images when none exist."""
        mock_get_all_images.return_value = []

        response = client.get("/images/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 0 images" in data["message"]
        assert data["data"] == []

    @patch("app.routes.images.db_get_all_images")
    def test_get_all_images_filter_tagged(
        self, mock_get_all_images, client, sample_image_data
    ):
        """Test filtering images by tagged status."""
        mock_get_all_images.return_value = [sample_image_data]

        response = client.get("/images/?tagged=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

        mock_get_all_images.assert_called_once_with(tagged=True)

    @patch("app.routes.images.db_get_all_images")
    def test_get_all_images_filter_untagged(self, mock_get_all_images, client):
        """Test filtering images by untagged status."""
        mock_get_all_images.return_value = []

        response = client.get("/images/?tagged=false")

        assert response.status_code == 200
        mock_get_all_images.assert_called_once_with(tagged=False)

    @patch("app.routes.images.db_get_all_images")
    def test_get_all_images_database_error(self, mock_get_all_images, client):
        """Test handling database errors during image retrieval."""
        mock_get_all_images.side_effect = Exception("Database connection failed")

        response = client.get("/images/")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    # ============================================================================
    # POST /images/toggle-favourite - Toggle Favourite Tests
    # ============================================================================

    @patch("app.routes.images.db_get_all_images")
    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_toggle_favourite_success(
        self, mock_toggle_fav, mock_get_all, client, sample_image_data
    ):
        """Test successfully toggling favourite status."""
        mock_toggle_fav.return_value = True
        # Return updated image with isFavourite=True
        updated_image = sample_image_data.copy()
        updated_image["isFavourite"] = True
        mock_get_all.return_value = [updated_image]

        request_data = {"image_id": "test-image-id-123"}

        response = client.post("/images/toggle-favourite", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["image_id"] == "test-image-id-123"
        assert data["isFavourite"] is True

        mock_toggle_fav.assert_called_once_with("test-image-id-123")

    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_toggle_favourite_not_found(self, mock_toggle_fav, client):
        """Test toggling favourite for non-existent image."""
        mock_toggle_fav.return_value = False

        request_data = {"image_id": "non-existent-id"}

        response = client.post("/images/toggle-favourite", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Image not found" in data["detail"]

    def test_toggle_favourite_missing_image_id(self, client):
        """Test toggling favourite without image_id field."""
        request_data = {}

        response = client.post("/images/toggle-favourite", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_toggle_favourite_database_error(self, mock_toggle_fav, client):
        """Test handling database errors during favourite toggle."""
        mock_toggle_fav.side_effect = Exception("Database error")

        request_data = {"image_id": "test-image-id-123"}

        response = client.post("/images/toggle-favourite", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]

    # ============================================================================
    # Edge Cases and Error Handling Tests
    # ============================================================================

    @patch("app.routes.images.db_get_all_images")
    def test_get_images_with_null_metadata(self, mock_get_all_images, client):
        """Test handling images with null/empty metadata."""
        mock_get_all_images.return_value = [
            {
                "id": "img-null-meta",
                "path": "/path/to/img.jpg",
                "folder_id": "folder-1",
                "thumbnailPath": "/path/to/thumb.jpg",
                "metadata": {},  # Empty metadata
                "isTagged": False,
                "isFavourite": False,
                "tags": None,
            }
        ]

        response = client.get("/images/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

    @patch("app.routes.images.db_get_all_images")
    def test_get_images_with_location_metadata(self, mock_get_all_images, client):
        """Test images with GPS location metadata."""
        mock_get_all_images.return_value = [
            {
                "id": "img-with-location",
                "path": "/path/to/gps_img.jpg",
                "folder_id": "folder-1",
                "thumbnailPath": "/path/to/thumb.jpg",
                "metadata": {
                    "name": "gps_img.jpg",
                    "date_created": "2024-01-01T12:00:00",
                    "width": 1920,
                    "height": 1080,
                    "file_location": "/path/to/gps_img.jpg",
                    "file_size": 1024000,
                    "item_type": "image/jpeg",
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                },
                "isTagged": True,
                "isFavourite": False,
                "tags": ["landscape"],
            }
        ]

        response = client.get("/images/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        first_image = data["data"][0]
        assert first_image["metadata"]["latitude"] == 37.7749
        assert first_image["metadata"]["longitude"] == -122.4194

    # ============================================================================
    # Integration & Workflow Tests
    # ============================================================================

    @patch("app.routes.images.db_get_all_images")
    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_toggle_and_verify_favourite(
        self, mock_toggle_fav, mock_get_all, client, sample_image_data
    ):
        """Test toggling favourite and verifying the change."""
        # Setup: Image starts as not favourite
        initial_image = sample_image_data.copy()
        initial_image["isFavourite"] = False

        # After toggle: Image becomes favourite
        updated_image = sample_image_data.copy()
        updated_image["isFavourite"] = True

        mock_toggle_fav.return_value = True
        mock_get_all.return_value = [updated_image]

        # Toggle favourite
        toggle_response = client.post(
            "/images/toggle-favourite", json={"image_id": "test-image-id-123"}
        )

        assert toggle_response.status_code == 200
        assert toggle_response.json()["isFavourite"] is True

        # Verify by getting all images
        mock_get_all.return_value = [updated_image]
        get_response = client.get("/images/")

        assert get_response.status_code == 200
        assert get_response.json()["data"][0]["isFavourite"] is True
