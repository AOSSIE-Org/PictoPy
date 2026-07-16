from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.models import router as models_router

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
