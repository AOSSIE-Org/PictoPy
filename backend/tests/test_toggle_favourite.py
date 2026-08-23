from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.images import router as images_router


@pytest.fixture
def client() -> TestClient:
    """Create a test client with the images router mounted."""
    app = FastAPI()
    app.include_router(images_router, prefix="/images")
    return TestClient(app)


class TestToggleFavourite:
    """Route-level tests for POST /images/toggle-favourite."""

    @patch("app.routes.images.db_get_image_by_id")
    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_success(
        self, mock_toggle: MagicMock, mock_get: MagicMock, client: TestClient
    ) -> None:
        mock_toggle.return_value = True
        mock_get.return_value = {"isFavourite": True}

        resp = client.post("/images/toggle-favourite", json={"image_id": "img-1"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["image_id"] == "img-1"
        assert body["isFavourite"] is True

    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_not_found(self, mock_toggle: MagicMock, client: TestClient) -> None:
        mock_toggle.return_value = False

        resp = client.post("/images/toggle-favourite", json={"image_id": "bad-id"})

        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert detail["success"] is False
        assert "error" in detail
        assert "message" in detail

    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_internal_error(self, mock_toggle: MagicMock, client: TestClient) -> None:
        mock_toggle.side_effect = Exception("db crashed")

        resp = client.post("/images/toggle-favourite", json={"image_id": "img-1"})

        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert detail["success"] is False
        assert detail["error"] == "Internal server error"
