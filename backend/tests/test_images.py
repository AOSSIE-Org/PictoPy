import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.images import router as images_router

app = FastAPI()
app.include_router(images_router, prefix="/images")
client = TestClient(app)


@pytest.fixture
def sample_image_id():
    return "image_123"


@pytest.fixture
def sample_image_path(tmp_path):
    image_file = tmp_path / "old_name.jpg"
    image_file.write_bytes(b"dummy image data")
    return str(image_file)


class TestRenameImageAPI:
    """Tests for the /images/rename-image endpoint."""

    @patch("app.routes.images.db_get_image_path_by_id")
    @patch("app.routes.images.os.rename")
    @patch("app.routes.images.os.open")
    def test_rename_image_success(
        self,
        mock_open,
        mock_rename,
        mock_get_path,
        sample_image_id,
        sample_image_path,
    ):
        mock_get_path.return_value = sample_image_path
        mock_open.return_value = 3  # dummy file descriptor

        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": "new_name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully renamed image" in data["message"]

        folder = os.path.dirname(sample_image_path)
        ext = os.path.splitext(sample_image_path)[1]
        expected_new_path = os.path.join(folder, "new_name" + ext)

        mock_get_path.assert_called_once_with(sample_image_id)
        mock_open.assert_called_once()
        mock_rename.assert_called_once_with(sample_image_path, expected_new_path)

    def test_rename_image_empty_id(self):
        response = client.put(
            "/images/rename-image",
            json={"image_id": "   ", "rename": "new_name"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "Image ID cannot be empty" in data["detail"]["message"]

    def test_rename_image_empty_name(self, sample_image_id):
        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": "   "},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "New image name cannot be empty" in data["detail"]["message"]

    @pytest.mark.parametrize(
        "invalid_char", ['*', '^', '!', '/', '\\', '?', '|', '<', '>', ':', '"']
    )
    def test_rename_image_invalid_characters(self, sample_image_id, invalid_char):
        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": f"bad{invalid_char}name"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"

    @patch("app.routes.images.db_get_image_path_by_id")
    def test_rename_image_not_found(self, mock_get_path, sample_image_id):
        mock_get_path.return_value = None

        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": "new_name"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Image Not Found"

    @patch("app.routes.images.db_get_image_path_by_id")
    @patch("app.routes.images.os.open")
    def test_rename_image_target_exists(
        self, mock_open, mock_get_path, sample_image_id, sample_image_path
    ):
        mock_get_path.return_value = sample_image_path
        mock_open.side_effect = FileExistsError()

        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": "new_name"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "File Exists"

    @patch("app.routes.images.db_get_image_path_by_id")
    @patch("app.routes.images.os.unlink")
    @patch("app.routes.images.os.rename")
    @patch("app.routes.images.os.open")
    def test_rename_image_unexpected_error(
        self,
        mock_open,
        mock_rename,
        mock_unlink,
        mock_get_path,
        sample_image_id,
        sample_image_path,
    ):
        mock_get_path.return_value = sample_image_path
        mock_open.return_value = 3
        mock_rename.side_effect = OSError("disk error")

        response = client.put(
            "/images/rename-image",
            json={"image_id": sample_image_id, "rename": "new_name"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"
        mock_unlink.assert_called_once()

