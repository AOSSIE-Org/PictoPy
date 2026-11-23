from unittest.mock import patch, MagicMock

import numpy as np

from app.utils.images import image_util_process_unembedded_images

BASE_METADATA = {
    "base": {
        "logit_scale": 4.724453449249268,
        "logit_bias": -16.771724700927734,
        "model_version": "siglip2-base-patch16-224",
        "input_resolution": 224,
    }
}


def _image(image_id: str) -> dict:
    return {
        "id": image_id,
        "path": f"/photos/{image_id}.jpg",
        "folder_id": "1",
        "thumbnailPath": "",
        "metadata": {},
    }


class TestProcessUnembeddedImages:
    @patch("app.database.images.db_get_unembedded_images")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_skips_entirely_when_vision_model_not_installed(
        self, mock_exists, mock_registry_keys, mock_get_path, mock_unembedded
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_get_path.return_value = "/nonexistent/vision.onnx"
        mock_exists.return_value = False

        image_util_process_unembedded_images()

        mock_unembedded.assert_not_called()

    @patch("app.database.images.db_get_unembedded_images")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_noop_when_nothing_to_embed(
        self, mock_exists, mock_registry_keys, mock_get_path, mock_unembedded
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_get_path.return_value = "/models/vision.onnx"
        mock_exists.return_value = True
        mock_unembedded.return_value = []

        with patch("app.models.SigLIP2Vision.SigLIP2Vision") as mock_vision_cls:
            image_util_process_unembedded_images()
            mock_vision_cls.assert_not_called()

    @patch("app.database.images.db_mark_images_embedded")
    @patch("app.database.image_embeddings.db_upsert_image_embeddings")
    @patch("app.models.SigLIP2Vision.SigLIP2Vision")
    @patch("app.utils.SigLIP.siglip_util_preprocess_image")
    @patch("app.database.images.db_get_unembedded_images")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_corrupt_images_excluded_from_embeddings_and_not_marked_embedded(
        self,
        mock_exists,
        mock_registry_keys,
        mock_get_path,
        mock_unembedded,
        mock_preprocess,
        mock_vision_cls,
        mock_upsert,
        mock_mark_embedded,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_get_path.return_value = "/models/vision.onnx"
        mock_exists.return_value = True

        images = [_image("img0"), _image("img1"), _image("img2")]
        mock_unembedded.return_value = images

        def preprocess_side_effect(path, resolution):
            # img1 is the "corrupt" one -- preprocessing fails for it alone.
            if "img1" in path:
                return None
            return np.zeros((3, 224, 224), dtype=np.float32)

        mock_preprocess.side_effect = preprocess_side_effect

        mock_vision_instance = MagicMock()
        mock_vision_instance.get_embedding.return_value = np.ones(
            (2, 768), dtype=np.float32
        )
        mock_vision_cls.return_value = mock_vision_instance

        with patch("app.config.settings.SIGLIP2_EMBED_BATCH_SIZE", 8), patch(
            "app.config.settings.SIGLIP2_SCORING_METADATA", BASE_METADATA
        ), patch("app.config.settings.SIGLIP2_ACTIVE_CHECKPOINT", "base"):
            image_util_process_unembedded_images()

        # Only the two successfully-preprocessed images get an embedding row.
        mock_upsert.assert_called_once()
        upserted_rows = mock_upsert.call_args[0][0]
        assert {row[0] for row in upserted_rows} == {"img0", "img2"}
        assert all(row[1] == "siglip2-base-patch16-224" for row in upserted_rows)

        # Only the successfully-preprocessed images are marked embedded. The
        # corrupt one stays isEmbedded=False so it's retried on a later pass
        # instead of being permanently excluded from semantic search if the
        # underlying issue (a transient lock, a restored backup) resolves.
        mock_mark_embedded.assert_called_once()
        assert set(mock_mark_embedded.call_args[0][0]) == {"img0", "img2"}

        mock_vision_instance.close.assert_called_once()

    @patch("app.database.images.db_mark_images_embedded")
    @patch("app.database.image_embeddings.db_upsert_image_embeddings")
    @patch("app.models.SigLIP2Vision.SigLIP2Vision")
    @patch("app.utils.SigLIP.siglip_util_preprocess_image")
    @patch("app.database.images.db_get_unembedded_images")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_batches_respect_configured_batch_size(
        self,
        mock_exists,
        mock_registry_keys,
        mock_get_path,
        mock_unembedded,
        mock_preprocess,
        mock_vision_cls,
        mock_upsert,
        mock_mark_embedded,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_get_path.return_value = "/models/vision.onnx"
        mock_exists.return_value = True

        images = [_image(f"img{i}") for i in range(5)]
        mock_unembedded.return_value = images
        mock_preprocess.return_value = np.zeros((3, 224, 224), dtype=np.float32)

        mock_vision_instance = MagicMock()
        mock_vision_instance.get_embedding.side_effect = lambda batch: np.ones(
            (len(batch), 768), dtype=np.float32
        )
        mock_vision_cls.return_value = mock_vision_instance

        with patch("app.config.settings.SIGLIP2_EMBED_BATCH_SIZE", 2), patch(
            "app.config.settings.SIGLIP2_SCORING_METADATA", BASE_METADATA
        ), patch("app.config.settings.SIGLIP2_ACTIVE_CHECKPOINT", "base"):
            image_util_process_unembedded_images()

        # 5 images at batch size 2 -> 3 batches (2, 2, 1).
        assert mock_upsert.call_count == 3
        assert mock_mark_embedded.call_count == 3
        total_upserted = sum(len(c.args[0]) for c in mock_upsert.call_args_list)
        assert total_upserted == 5

    @patch("app.database.images.db_mark_images_embedded")
    @patch("app.database.image_embeddings.db_upsert_image_embeddings")
    @patch("app.models.SigLIP2Vision.SigLIP2Vision")
    @patch("app.database.images.db_get_unembedded_images")
    @patch("app.models.model_registry.get_model_path")
    @patch("app.models.model_registry.get_siglip2_registry_keys")
    @patch("os.path.exists")
    def test_vision_model_closed_even_if_embedding_raises(
        self,
        mock_exists,
        mock_registry_keys,
        mock_get_path,
        mock_unembedded,
        mock_vision_cls,
        mock_upsert,
        mock_mark_embedded,
    ):
        mock_registry_keys.return_value = ("siglip2_base_vision", "siglip2_base_text")
        mock_get_path.return_value = "/models/vision.onnx"
        mock_exists.return_value = True
        mock_unembedded.return_value = [_image("img0")]

        mock_vision_instance = MagicMock()
        mock_vision_instance.get_embedding.side_effect = RuntimeError("boom")
        mock_vision_cls.return_value = mock_vision_instance

        with patch(
            "app.utils.SigLIP.siglip_util_preprocess_image",
            return_value=np.zeros((3, 224, 224), dtype=np.float32),
        ), patch("app.config.settings.SIGLIP2_EMBED_BATCH_SIZE", 8), patch(
            "app.config.settings.SIGLIP2_SCORING_METADATA", BASE_METADATA
        ), patch(
            "app.config.settings.SIGLIP2_ACTIVE_CHECKPOINT", "base"
        ):
            # The function catches and logs internally -- it must not raise,
            # and must still release the vision model session.
            image_util_process_unembedded_images()

        mock_vision_instance.close.assert_called_once()
        mock_upsert.assert_not_called()
