from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.images import router as images_router

app = FastAPI()
app.include_router(images_router, prefix="/images")
client = TestClient(app)


class TestImagesAPI:
    @patch("app.routes.images.db_get_image_by_id")
    @patch("app.routes.images.db_toggle_image_favourite_status")
    def test_toggle_favourite_uses_single_image_lookup(
        self, mock_toggle_favourite, mock_get_image_by_id
    ):
        image_id = "img_123"
        mock_toggle_favourite.return_value = True
        mock_get_image_by_id.return_value = {
            "id": image_id,
            "isFavourite": True,
        }

        response = client.post("/images/toggle-favourite", json={"image_id": image_id})

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "image_id": image_id,
            "isFavourite": True,
        }

        mock_toggle_favourite.assert_called_once_with(image_id)
        mock_get_image_by_id.assert_called_once_with(image_id)
