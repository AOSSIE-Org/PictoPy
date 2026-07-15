import json
from unittest.mock import patch, MagicMock

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.images import router as images_router

app = FastAPI()
app.include_router(images_router, prefix="/images")
client = TestClient(app)

BASE_METADATA = {
    "base": {
        "logit_scale": 4.724453449249268,
        "logit_bias": -16.771724700927734,
        "model_version": "siglip2-base-patch16-224",
        "input_resolution": 224,
    }
}


def _image_row(image_id: str, path: str) -> dict:
    return {
        "id": image_id,
        "path": path,
        "folder_id": "1",
        "thumbnailPath": f"{path}.thumb",
        "metadata": json.dumps(
            {
                "name": path,
                "date_created": None,
                "width": 100,
                "height": 100,
                "file_location": path,
                "file_size": 12345,
                "item_type": "image/jpeg",
            }
        ),
        "isTagged": True,
        "isFavourite": False,
        "tags": None,
    }


class TestSemanticSearchEndpoint:
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_text_model_not_installed_returns_404(
        self, mock_exists, mock_registry_keys, mock_tok_key, mock_get_path
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.return_value = "/does/not/exist.onnx"
        mock_exists.return_value = False

        response = client.get("/images/semantic-search", params={"query": "beach"})

        assert response.status_code == 404
        assert "not installed" in response.json()["detail"]["message"]

    @patch("app.database.image_embeddings.db_get_all_embeddings")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_no_embeddings_returns_friendly_empty_success(
        self,
        mock_exists,
        mock_registry_keys,
        mock_tok_key,
        mock_get_path,
        mock_get_all_embeddings,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.return_value = "/models/text.onnx"
        mock_exists.return_value = True
        mock_get_all_embeddings.return_value = ([], np.empty((0, 0), dtype=np.float32))

        response = client.get("/images/semantic-search", params={"query": "beach"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
        assert "No images have been embedded" in data["message"]

    @patch("app.database.images.db_get_images_by_ids")
    @patch("app.utils.SigLIP.siglip_util_get_text_model")
    @patch("app.utils.SigLIP.siglip_util_tokenize_query")
    @patch("app.database.image_embeddings.db_get_all_embeddings")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_returns_matches_above_threshold_sorted_desc(
        self,
        mock_exists,
        mock_registry_keys,
        mock_tok_key,
        mock_get_path,
        mock_get_all_embeddings,
        mock_tokenize,
        mock_get_text_model,
        mock_get_images_by_ids,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.return_value = "/models/text.onnx"
        mock_exists.return_value = True

        # img_high's embedding is aligned with the query vector (dot=1),
        # img_low's is orthogonal (dot=0) -- only img_high should clear the
        # match threshold once run through the calibrated sigmoid scoring.
        mock_get_all_embeddings.return_value = (
            ["img_high", "img_low"],
            np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        )
        mock_tokenize.return_value = (
            np.zeros((1, 64), dtype=np.int64),
            np.ones((1, 64), dtype=np.int64),
        )

        mock_text_model = MagicMock()
        mock_text_model.get_embedding.return_value = np.array(
            [1.0, 0.0], dtype=np.float32
        )
        mock_get_text_model.return_value = mock_text_model

        mock_get_images_by_ids.return_value = [_image_row("img_high", "/p/high.jpg")]

        with patch(
            "app.config.settings.SIGLIP2_SCORING_METADATA", BASE_METADATA
        ), patch("app.config.settings.SIGLIP2_ACTIVE_CHECKPOINT", "base"), patch(
            "app.config.settings.SIGLIP2_MATCH_THRESHOLD", 0.01
        ), patch(
            "app.config.settings.SIGLIP2_QUERY_TEMPLATE", "This is a photo of {query}."
        ):
            response = client.get(
                "/images/semantic-search", params={"query": "  Beach  "}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["images"][0]["id"] == "img_high"
        assert data["data"]["images"][0]["score"] > 0.9

        # Query must be stripped + lowercased before templating, so casing/
        # whitespace differences hit the calibration-validated regime.
        mock_tokenize.assert_called_once_with("This is a photo of beach.")
        mock_get_images_by_ids.assert_called_once_with(["img_high"])

    @patch("app.database.image_embeddings.db_get_all_embeddings")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_whitespace_only_query_returns_400(
        self,
        mock_exists,
        mock_registry_keys,
        mock_tok_key,
        mock_get_path,
        mock_get_all_embeddings,
    ):
        # min_length=1 on the FastAPI Query param only checks raw string
        # length, so a whitespace-only query slips past it -- the route's
        # own strip().lower() + empty-check is what should catch this.
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.return_value = "/models/text.onnx"
        mock_exists.return_value = True
        mock_get_all_embeddings.return_value = (
            ["img1"],
            np.array([[1.0, 0.0]], dtype=np.float32),
        )

        response = client.get("/images/semantic-search", params={"query": "   "})

        assert response.status_code == 400

    @patch("app.database.images.db_get_images_by_ids")
    @patch("app.utils.SigLIP.siglip_util_get_text_model")
    @patch("app.utils.SigLIP.siglip_util_tokenize_query")
    @patch("app.database.image_embeddings.db_get_all_embeddings")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_all_scores_below_threshold_returns_empty_results(
        self,
        mock_exists,
        mock_registry_keys,
        mock_tok_key,
        mock_get_path,
        mock_get_all_embeddings,
        mock_tokenize,
        mock_get_text_model,
        mock_get_images_by_ids,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.return_value = "/models/text.onnx"
        mock_exists.return_value = True

        # Orthogonal query vector -> dot product 0 for every stored
        # embedding -> every score sinks well below SIGLIP2_MATCH_THRESHOLD.
        mock_get_all_embeddings.return_value = (
            ["img_a"],
            np.array([[1.0, 0.0]], dtype=np.float32),
        )
        mock_tokenize.return_value = (
            np.zeros((1, 64), dtype=np.int64),
            np.ones((1, 64), dtype=np.int64),
        )
        mock_text_model = MagicMock()
        mock_text_model.get_embedding.return_value = np.array(
            [0.0, 1.0], dtype=np.float32
        )
        mock_get_text_model.return_value = mock_text_model

        with patch(
            "app.config.settings.SIGLIP2_SCORING_METADATA", BASE_METADATA
        ), patch("app.config.settings.SIGLIP2_ACTIVE_CHECKPOINT", "base"), patch(
            "app.config.settings.SIGLIP2_MATCH_THRESHOLD", 0.01
        ), patch(
            "app.config.settings.SIGLIP2_QUERY_TEMPLATE", "This is a photo of {query}."
        ):
            response = client.get(
                "/images/semantic-search", params={"query": "nonsense"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
        assert data["data"]["images"] == []
        mock_get_images_by_ids.assert_not_called()
