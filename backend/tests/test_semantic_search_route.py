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

    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_tokenizer_key")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_tokenizer_not_installed_returns_404(
        self, mock_exists, mock_registry_keys, mock_tok_key, mock_get_path
    ):
        # Text model IS present, but the tokenizer is missing -- this must
        # be checked and reported independently of the text model check.
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_tok_key.return_value = "siglip2_base_tokenizer"
        mock_get_path.side_effect = lambda key: {
            "siglip2_base_text": "/models/text.onnx",
            "siglip2_base_tokenizer": "/models/tokenizer.json",
        }[key]
        mock_exists.side_effect = lambda path: path == "/models/text.onnx"

        response = client.get("/images/semantic-search", params={"query": "beach"})

        assert response.status_code == 404
        assert "tokenizer" in response.json()["detail"]["message"].lower()

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

        # Two embeddings that both clear SIGLIP2_MATCH_THRESHOLD (0.01) with
        # clearly distinct scores after 4dp rounding (dot=0.16 -> ~0.7782,
        # dot=0.13 -> ~0.1067 -- realistic dot-product magnitudes per the
        # calibrated scoring, not the near-1.0/near-0.0 saturation you'd get
        # from naive orthogonal/aligned toy vectors). img_high has the
        # *lower* score despite being listed first in db_get_all_embeddings,
        # so a broken sort would put it first in the response too.
        mock_get_all_embeddings.return_value = (
            ["img_high", "img_highest"],
            np.array([[0.13, 0.0], [0.16, 0.0]], dtype=np.float32),
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

        # db_get_images_by_ids preserves caller-supplied ID order in the
        # real implementation (verified in test_image_embeddings.py's
        # sibling tests) -- mirror that contract here rather than asserting
        # the route re-sorts independently. It doesn't: matched_pairs is
        # sorted once, and everything downstream (matched_ids, the DB call,
        # the response) just follows that order through.
        mock_get_images_by_ids.side_effect = lambda ids: [
            _image_row(img_id, f"/p/{img_id}.jpg") for img_id in ids
        ]

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
        assert data["data"]["total"] == 2
        assert data["data"]["images"][0]["id"] == "img_highest"
        assert data["data"]["images"][1]["id"] == "img_high"
        assert data["data"]["images"][0]["score"] > data["data"]["images"][1]["score"]

        # Query must be stripped + lowercased before templating, so casing/
        # whitespace differences hit the calibration-validated regime.
        mock_tokenize.assert_called_once_with("This is a photo of beach.")
        # The definitive proof of correct sorting: matched_ids (built from
        # matched_pairs.sort(..., reverse=True)) must already be in
        # descending-score order by the time it reaches this call.
        mock_get_images_by_ids.assert_called_once_with(["img_highest", "img_high"])

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
