import json
from unittest.mock import patch, AsyncMock, MagicMock, call
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.models import (
    router as models_router,
    submit_embedding_backfill_if_semantic,
)
from app.utils.images import image_util_process_unembedded_images
from app.utils.semantic_labels import (
    semantic_util_build_label_embeddings,
    semantic_util_score_images,
)

app = FastAPI()
app.include_router(models_router, prefix="/models")
client = TestClient(app)


class TestModelsAPI:

    def test_delete_model_not_found(self):
        response = client.delete("/models/invalid_key")
        assert response.status_code == 404
        assert "not found in registry" in response.json()["detail"]

    @patch(
        "app.routes.models.MODEL_REGISTRY",
        {"facenet": {"tier": "required", "filename": "facenet.onnx"}},
    )
    def test_delete_required_model(self):
        response = client.delete("/models/facenet")
        assert response.status_code == 409
        assert "Cannot delete a required model" in response.json()["detail"]

    @patch(
        "app.routes.models.MODEL_REGISTRY",
        {"yolov8s": {"tier": "small", "filename": "yolov8s.onnx"}},
    )
    @patch("app.routes.models.db_get_metadata")
    def test_delete_active_tier_model(self, mock_get_metadata):
        mock_get_metadata.return_value = {
            "user_preferences": {"YOLO_model_size": "small"}
        }
        response = client.delete("/models/yolov8s")
        assert response.status_code == 409
        assert "currently active" in response.json()["detail"]

    @patch(
        "app.routes.models.MODEL_REGISTRY",
        {"yolov8s_face": {"tier": "small", "filename": "yolov8s_face.onnx"}},
    )
    @patch("app.routes.models.db_get_metadata")
    def test_delete_active_tier_face_model(self, mock_get_metadata):
        mock_get_metadata.return_value = {
            "user_preferences": {"YOLO_model_size": "small"}
        }
        response = client.delete("/models/yolov8s_face")
        assert response.status_code == 409
        assert "currently active" in response.json()["detail"]

    @patch(
        "app.routes.models.MODEL_REGISTRY",
        {"yolov8n": {"tier": "nano", "filename": "yolov8n.onnx"}},
    )
    @patch("app.routes.models.db_get_metadata")
    @patch("app.routes.models.try_mark_model_for_deletion")
    @patch("app.routes.models.get_model_path")
    def test_delete_model_in_use(self, mock_get_path, mock_try_mark, mock_get_metadata):
        mock_get_metadata.return_value = {
            "user_preferences": {"YOLO_model_size": "small"}
        }
        mock_try_mark.return_value = 2  # 2 active sessions
        mock_get_path.return_value = "/path/to/model"

        response = client.delete("/models/yolov8n")

        assert response.status_code == 409
        assert "currently in use by 2 active session" in response.json()["detail"]

    @patch(
        "app.routes.models.MODEL_REGISTRY",
        {"yolov8n": {"tier": "nano", "filename": "yolov8n.onnx"}},
    )
    @patch("app.routes.models.db_get_metadata")
    @patch("app.routes.models.try_mark_model_for_deletion")
    @patch("app.routes.models.release_model_deletion_mark")
    @patch("app.routes.models.get_model_path")
    @patch("os.path.exists")
    @patch("asyncio.to_thread")
    def test_delete_model_success(
        self,
        mock_to_thread,
        mock_exists,
        mock_get_path,
        mock_release,
        mock_try_mark,
        mock_get_metadata,
    ):
        mock_get_metadata.return_value = {
            "user_preferences": {"YOLO_model_size": "small"}
        }
        mock_try_mark.return_value = None
        mock_get_path.return_value = "/path/to/model"
        mock_exists.return_value = True

        response = client.delete("/models/yolov8n")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]

        mock_to_thread.assert_called_once()
        mock_release.assert_called_once_with("yolov8n")


class TestEmbeddingBackfillTrigger:
    """Semantic model installs must trigger the embedding backfill pass."""

    def test_helper_submits_pass_for_semantic_keys(self):
        executor = MagicMock()
        submit_embedding_backfill_if_semantic(
            ["siglip2_base_vision", "siglip2_base_text", "facenet"], executor
        )
        executor.submit.assert_has_calls(
            [
                call(semantic_util_build_label_embeddings),
                call(image_util_process_unembedded_images),
                call(semantic_util_score_images),
            ]
        )

    def test_helper_ignores_non_semantic_keys(self):
        executor = MagicMock()
        submit_embedding_backfill_if_semantic(["yolo_nano", "facenet"], executor)
        executor.submit.assert_not_called()

    @staticmethod
    def _drain_until_complete(local_client, task_id):
        """Read the SSE progress stream until the background task finishes."""
        with local_client.stream(
            "GET", f"/models/download/{task_id}/progress"
        ) as response:
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                msg = json.loads(line[len("data:") :])
                assert msg["status"] != "error", msg
                if msg["status"] == "complete":
                    return
        raise AssertionError("SSE stream ended without a 'complete' event")

    def _run_setup(self, tier: str) -> MagicMock:
        executor = MagicMock()
        with patch.object(app.state, "executor", executor, create=True), patch(
            "app.routes.models.ensure_model", new=AsyncMock()
        ):
            with TestClient(app) as local_client:
                response = local_client.post("/models/setup", json={"tier": tier})
                assert response.status_code == 200
                self._drain_until_complete(local_client, response.json()["task_id"])
        return executor

    def test_setup_semantic_tier_triggers_backfill(self):
        executor = self._run_setup("semantic")
        executor.submit.assert_has_calls(
            [
                call(semantic_util_build_label_embeddings),
                call(image_util_process_unembedded_images),
                call(semantic_util_score_images),
            ]
        )

    def test_setup_yolo_tier_does_not_trigger_backfill(self):
        executor = self._run_setup("nano")
        executor.submit.assert_not_called()

    def test_single_model_download_of_semantic_model_triggers_backfill(self):
        executor = MagicMock()
        with patch.object(app.state, "executor", executor, create=True), patch(
            "app.routes.models.ensure_model", new=AsyncMock()
        ):
            with TestClient(app) as local_client:
                response = local_client.post("/models/download/siglip2_base_vision")
                assert response.status_code == 200
                self._drain_until_complete(local_client, response.json()["task_id"])
        executor.submit.assert_has_calls(
            [
                call(semantic_util_build_label_embeddings),
                call(image_util_process_unembedded_images),
                call(semantic_util_score_images),
            ]
        )
