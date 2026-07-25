import os
import asyncio
import sys
import json
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock, call

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes.models import (
    router as models_router,
    DownloadTaskEntry,
    submit_embedding_backfill_if_semantic,
)
import app.routes.models as models_module
from app.utils.images import image_util_process_unembedded_images
from app.utils.semantic_labels import (
    semantic_util_build_label_embeddings,
    semantic_util_score_images,
)

app = FastAPI()
app.include_router(models_router, prefix="/models", tags=["models"])

client = TestClient(app)


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture
def mock_model_registry():
    # Keys match MODEL_REGISTRY structure — "filename" not "name"
    # The route does: spec["filename"] → response "name" field
    return {
        "yolo_nano": {
            "filename": "YOLOv11_Nano.onnx",
            "url": "https://example.com/models/YOLOv11_Nano.onnx",
            "sha256": "fake_sha256_yolo_nano",
            "feature": "object_detection",
            "tier": "nano",
            "size_mb": 10.2,
        },
        "yolo_nano_face": {
            "filename": "YOLOv11_Nano_Face.onnx",
            "url": "https://example.com/models/YOLOv11_Nano_Face.onnx",
            "sha256": "fake_sha256_yolo_nano_face",
            "feature": "face_detection",
            "tier": "nano",
            "size_mb": 10.1,
        },
        "yolo_small": {
            "filename": "YOLOv11_Small.onnx",
            "url": "https://example.com/models/YOLOv11_Small.onnx",
            "sha256": "fake_sha256_yolo_small",
            "feature": "object_detection",
            "tier": "small",
            "size_mb": 36.2,
        },
        "yolo_small_face": {
            "filename": "YOLOv11_Small_Face.onnx",
            "url": "https://example.com/models/YOLOv11_Small_Face.onnx",
            "sha256": "fake_sha256_yolo_small_face",
            "feature": "face_detection",
            "tier": "small",
            "size_mb": 36.1,
        },
        "yolo_medium": {
            "filename": "YOLOv11_Medium.onnx",
            "url": "https://example.com/models/YOLOv11_Medium.onnx",
            "sha256": "fake_sha256_yolo_medium",
            "feature": "object_detection",
            "tier": "medium",
            "size_mb": 76.9,
        },
        "yolo_medium_face": {
            "filename": "YOLOv11_Medium_Face.onnx",
            "url": "https://example.com/models/YOLOv11_Medium_Face.onnx",
            "sha256": "fake_sha256_yolo_medium_face",
            "feature": "face_detection",
            "tier": "medium",
            "size_mb": 76.6,
        },
        "facenet": {
            "filename": "FaceNet_128D.onnx",
            "url": "https://example.com/models/FaceNet_128D.onnx",
            "sha256": "fake_sha256_facenet",
            "feature": "face_embedding",
            "tier": "required",
            "size_mb": 87.0,
        },
    }


@pytest.fixture
def mock_model_registry_with_placeholder(mock_model_registry):
    # Mirrors the real registry's not-yet-uploaded entries (e.g. siglip2_large_vision),
    # which /status must exclude from its response.
    registry = dict(mock_model_registry)
    registry["siglip2_large_vision"] = {
        "filename": "SigLIP2_Large_Vision.onnx",
        "url": "PLACEHOLDER_URL",
        "sha256": "PLACEHOLDER_SHA256",
        "feature": "semantic_vision",
        "tier": "medium",
        "size_mb": 0,
    }
    return registry


@pytest.fixture
def mock_hardware_info():
    return {
        "ram_gb": 15.32,
        "gpu_detected": True,
        "gpu_names": ["NVIDIA GeForce RTX 3050 6GB Laptop GPU"],
        "apple_silicon": None,
        "available_providers": ["AzureExecutionProvider", "CPUExecutionProvider"],
        "recommended_tier": "medium",
    }


@pytest.fixture
def hardware_response(mock_hardware_info):
    with patch("app.routes.models.get_hardware_info", return_value=mock_hardware_info):
        return client.get("/models/hardware")


@pytest.fixture(autouse=True)
def clear_download_tasks():
    # Runs before every test ensures no leftover task IDs bleed between tests
    models_module.download_tasks.clear()
    yield
    models_module.download_tasks.clear()


@pytest.fixture
def completed_task_id():
    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    queue.put_nowait({"status": "complete", "model_key": "facenet"})

    mock_task = MagicMock()
    mock_task.done.return_value = True

    models_module.download_tasks[task_id] = DownloadTaskEntry(
        queue=queue,
        task=mock_task,
    )
    return task_id


@pytest.fixture
def error_task_id():
    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    queue.put_nowait({"status": "error", "message": "download failed"})

    mock_task = MagicMock()
    mock_task.done.return_value = True

    models_module.download_tasks[task_id] = DownloadTaskEntry(
        queue=queue,
        task=mock_task,
    )
    return task_id


@pytest.fixture
def active_listener_task_id():
    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()

    mock_task = MagicMock()
    mock_task.done.return_value = False

    entry = DownloadTaskEntry(queue=queue, task=mock_task)
    entry.active_listeners = 1  # simulate an existing listener

    models_module.download_tasks[task_id] = entry
    return task_id


@pytest.fixture
def completed_task_response(completed_task_id):
    return client.get(
        f"/models/download/{completed_task_id}/progress",
        headers={"Accept": "text/event-stream"},
    )


@pytest.fixture
def error_task_response(error_task_id):
    return client.get(
        f"/models/download/{error_task_id}/progress",
        headers={"Accept": "text/event-stream"},
    )


@pytest.fixture
def mock_tier_models():
    return {
        "nano": ["yolo_nano", "yolo_nano_face"],
        "small": ["yolo_small", "yolo_small_face"],
        "medium": ["yolo_medium", "yolo_medium_face"],
        "required": ["facenet"],
    }


@pytest.fixture
def setup_nano_response(mock_tier_models):
    with patch("app.routes.models.TIER_MODELS", mock_tier_models), patch(
        "app.routes.models.ensure_model", return_value=None
    ):
        return client.post("/models/setup", json={"tier": "nano"})


@pytest.fixture
def setup_required_response(mock_tier_models):
    with patch("app.routes.models.TIER_MODELS", mock_tier_models), patch(
        "app.routes.models.ensure_model", return_value=None
    ):
        return client.post("/models/setup", json={"tier": "required"})


@pytest.fixture
def download_facenet_response(mock_model_registry):
    with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
        "app.routes.models.ensure_model", return_value=None
    ):
        return client.post("/models/download/facenet")


# ##############################
# Test Classes — endpoints not covered upstream
# ##############################


class TestModelStatus:
    """Tests suite for GET /models/status"""

    def test_returns_200(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.status_code == 200

    def test_success_is_true(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.json()["success"] is True

    def test_data_is_object(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert isinstance(response.json()["data"], dict)

    def test_all_7_models_present(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            data = response.json()["data"]
            expected = [
                "yolo_nano",
                "yolo_nano_face",
                "yolo_small",
                "yolo_small_face",
                "yolo_medium",
                "yolo_medium_face",
                "facenet",
            ]
            for key in expected:
                assert key in data, f"Missing model key: {key}"

    def test_each_model_has_required_fields(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert "name" in model
                assert "installed" in model
                assert "feature" in model
                assert "tier" in model
                assert "size_mb" in model

    def test_installed_is_always_boolean(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert isinstance(model["installed"], bool)

    def test_installed_true_when_file_exists(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=True):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["installed"] is True

    def test_installed_false_when_file_missing(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["installed"] is False

    def test_tier_values_are_valid(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            valid_tiers = ["nano", "small", "medium", "required"]
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["tier"] in valid_tiers

    def test_facenet_tier_is_required(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.json()["data"]["facenet"]["tier"] == "required"

    def test_size_mb_is_positive_number(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert isinstance(model["size_mb"], (int, float))
                assert model["size_mb"] > 0

    def test_name_field_matches_filename(self, mock_model_registry):
        # Route maps spec["filename"] → response field "name"
        # Verifying the mapping is correct
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            data = response.json()["data"]
            assert data["facenet"]["name"] == "FaceNet_128D.onnx"
            assert data["yolo_nano"]["name"] == "YOLOv11_Nano.onnx"

    def test_placeholder_models_excluded_from_status(
        self, mock_model_registry_with_placeholder
    ):
        # Entries with PLACEHOLDER_URL / PLACEHOLDER_SHA256 (not-yet-uploaded
        # models) must not appear in /status.
        with patch(
            "app.routes.models.MODEL_REGISTRY", mock_model_registry_with_placeholder
        ), patch(
            "app.routes.models.get_model_path", return_value="/fake/path.onnx"
        ), patch(
            "app.routes.models.os.path.exists", return_value=False
        ):
            response = client.get("/models/status")
            data = response.json()["data"]
            assert "siglip2_large_vision" not in data
            assert "yolo_nano" in data


class TestHardwareInformation:
    """Test suite for GET /models/hardware."""

    def test_returns_200(self, hardware_response):
        assert hardware_response.status_code == 200

    def test_success_is_true(self, hardware_response):
        json_response = hardware_response.json()
        assert json_response["success"] is True

    def test_data_is_object(self, hardware_response):
        json_response = hardware_response.json()
        data = json_response["data"]
        assert isinstance(data, dict)

    def test_data_has_required_fields(self, hardware_response):
        json_response = hardware_response.json()
        data = json_response["data"]
        assert "ram_gb" in data
        assert "gpu_detected" in data
        assert "gpu_names" in data
        assert "apple_silicon" in data
        assert "available_providers" in data
        assert "recommended_tier" in data

    def test_ram_is_positive_number(self, hardware_response):
        json_response = hardware_response.json()
        ram = json_response["data"]["ram_gb"]
        assert isinstance(ram, (int, float))
        assert ram > 0

    def test_ram_gb_is_realistic(self, hardware_response):
        json_response = hardware_response.json()
        ram = json_response["data"]["ram_gb"]
        assert 0.5 <= ram <= 2048

    def test_gpu_is_boolean(self, hardware_response):
        json_response = hardware_response.json()
        gpu_detected = json_response["data"]["gpu_detected"]
        assert isinstance(gpu_detected, bool)

    def test_gpu_names_is_array(self, hardware_response):
        json_response = hardware_response.json()
        gpu_names = json_response["data"]["gpu_names"]
        assert isinstance(gpu_names, list)

    def test_gpu_names_contains_strings(self, hardware_response):
        json_response = hardware_response.json()
        gpu_names = json_response["data"]["gpu_names"]
        for gpu in gpu_names:
            assert isinstance(gpu, str)

    def test_apple_silicon_type(self, hardware_response):
        json_response = hardware_response.json()
        apple_silicon = json_response["data"]["apple_silicon"]
        assert apple_silicon is None or isinstance(apple_silicon, bool)

    def test_cpu_provider_always_present(self, hardware_response):
        json_response = hardware_response.json()
        providers = json_response["data"]["available_providers"]
        assert "CPUExecutionProvider" in providers

    def test_available_providers_is_non_empty_array(self, hardware_response):
        json_response = hardware_response.json()
        providers = json_response["data"]["available_providers"]
        assert isinstance(providers, list)
        assert len(providers) > 0

    def test_available_providers_contains_strings(self, hardware_response):
        json_response = hardware_response.json()
        providers = json_response["data"]["available_providers"]
        for provider in providers:
            assert isinstance(provider, str)

    def test_recommended_tier_is_valid(self, hardware_response):
        json_response = hardware_response.json()
        recommended_tier = json_response["data"]["recommended_tier"]
        assert recommended_tier in ["nano", "small", "medium"]

    def test_recommended_tier_is_string(self, hardware_response):
        json_response = hardware_response.json()
        recommended_tier = json_response["data"]["recommended_tier"]
        assert isinstance(recommended_tier, str)

    def test_gpu_detected_true_means_names_not_empty(self, hardware_response):
        json_response = hardware_response.json()
        data = json_response["data"]
        gpu_detected = data["gpu_detected"]
        gpu_names = data["gpu_names"]
        if gpu_detected is True:
            assert len(gpu_names) > 0

    def test_apple_silicon_and_gpu_mutually_exclusive(self, hardware_response):
        json_response = hardware_response.json()
        data = json_response["data"]
        apple_silicon = data["apple_silicon"]
        gpu_detected = data["gpu_detected"]
        if apple_silicon is True:
            assert gpu_detected is False

    def test_post_method_not_allowed(self):
        response = client.post("/models/hardware")
        assert response.status_code == 405

    def test_returns_500_when_hardware_detection_fails(self):
        with patch(
            "app.routes.models.get_hardware_info",
            side_effect=Exception("hardware error"),
        ):
            response = client.get("/models/hardware")
            assert response.status_code == 500

    def test_no_gpu_returns_empty_gpu_names(self):
        mock_no_gpu = {
            "ram_gb": 8.0,
            "gpu_detected": False,
            "gpu_names": [],
            "apple_silicon": None,
            "available_providers": ["CPUExecutionProvider"],
            "recommended_tier": "small",
        }
        with patch("app.routes.models.get_hardware_info", return_value=mock_no_gpu):
            response = client.get("/models/hardware")
            json_response = response.json()
            data = json_response["data"]
            gpu_detected = data["gpu_detected"]
            gpu_names = data["gpu_names"]
            assert gpu_detected is False
            assert gpu_names == []


class TestDownloadProgress:
    """Tests for GET /models/download/{task_id}/progress"""

    # --- Status code tests ---

    def test_returns_200_for_valid_task(self, completed_task_response):
        assert completed_task_response.status_code == 200

    def test_returns_404_for_unknown_task_id(self):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/models/download/{fake_id}/progress")
        assert response.status_code == 404

    def test_returns_404_error_message(self):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/models/download/{fake_id}/progress")
        json_response = response.json()
        detail = json_response["detail"]
        assert "not found" in detail.lower()

    def test_returns_409_when_listener_already_active(self, active_listener_task_id):
        response = client.get(f"/models/download/{active_listener_task_id}/progress")
        assert response.status_code == 409

    # --- Content type tests ---

    def test_content_type_is_event_stream(self, completed_task_response):
        content_type = completed_task_response.headers["content-type"]
        assert "text/event-stream" in content_type

    # --- Response body tests ---

    def test_response_body_is_not_empty(self, completed_task_response):
        raw = completed_task_response.text
        assert isinstance(raw, str)
        assert len(raw) > 0

    def test_response_starts_with_data_prefix(self, completed_task_response):
        raw = completed_task_response.text
        assert "data:" in raw

    def test_stream_data_is_valid_json(self, completed_task_response):
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                assert isinstance(parsed, dict)

    def test_stream_data_has_status_field(self, completed_task_response):
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                assert "status" in parsed

    def test_status_is_valid_value(self, completed_task_response):
        valid_statuses = ["downloading", "complete", "error"]
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                status = parsed["status"]
                assert status in valid_statuses

    # --- Completed task specific tests ---

    def test_completed_stream_has_model_key(self, completed_task_response):
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                if parsed["status"] == "complete":
                    assert "model_key" in parsed

    def test_completed_stream_model_key_is_string(self, completed_task_response):
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                if parsed["status"] == "complete":
                    model_key = parsed["model_key"]
                    assert isinstance(model_key, str)

    def test_completed_stream_model_key_value(self, completed_task_response):
        raw = completed_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                if parsed["status"] == "complete":
                    model_key = parsed["model_key"]
                    assert model_key == "facenet"

    # --- Error task specific tests ---

    def test_error_stream_contains_error_status(self, error_task_response):
        raw = error_task_response.text
        assert "error" in raw

    def test_error_stream_has_message_field(self, error_task_response):
        raw = error_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                if parsed["status"] == "error":
                    assert "message" in parsed

    def test_error_stream_message_is_string(self, error_task_response):
        raw = error_task_response.text
        for line in raw.strip().split("\n"):
            if line.startswith("data:"):
                json_part = line[len("data:") :].strip()
                parsed = json.loads(json_part)
                if parsed["status"] == "error":
                    message = parsed["message"]
                    assert isinstance(message, str)


class TestSetupModels:
    """Tests for POST /models/setup"""

    # --- Valid tiers ---

    def test_nano_tier_returns_200(self, setup_nano_response):
        assert setup_nano_response.status_code == 200

    def test_small_tier_returns_200(self, mock_tier_models):
        with patch("app.routes.models.TIER_MODELS", mock_tier_models), patch(
            "app.routes.models.ensure_model", return_value=None
        ):
            response = client.post("/models/setup", json={"tier": "small"})
            assert response.status_code == 200

    def test_medium_tier_returns_200(self, mock_tier_models):
        with patch("app.routes.models.TIER_MODELS", mock_tier_models), patch(
            "app.routes.models.ensure_model", return_value=None
        ):
            response = client.post("/models/setup", json={"tier": "medium"})
            assert response.status_code == 200

    def test_required_tier_returns_200(self, setup_required_response):
        assert setup_required_response.status_code == 200

    # --- Response structure ---

    def test_success_is_true(self, setup_nano_response):
        json_response = setup_nano_response.json()
        assert json_response["success"] is True

    def test_response_has_task_id(self, setup_nano_response):
        json_response = setup_nano_response.json()
        assert "task_id" in json_response

    def test_task_id_is_valid_uuid(self, setup_nano_response):
        json_response = setup_nano_response.json()
        task_id = json_response["task_id"]
        uuid.UUID(task_id)

    def test_response_has_message(self, setup_nano_response):
        json_response = setup_nano_response.json()
        assert "message" in json_response

    def test_message_contains_tier_name(self, setup_nano_response):
        json_response = setup_nano_response.json()
        message = json_response["message"]
        assert "nano" in message

    def test_each_call_gets_unique_task_id(self, mock_tier_models):
        with patch("app.routes.models.TIER_MODELS", mock_tier_models), patch(
            "app.routes.models.ensure_model", return_value=None
        ):
            response_1 = client.post("/models/setup", json={"tier": "nano"})
            response_2 = client.post("/models/setup", json={"tier": "nano"})
            task_id_1 = response_1.json()["task_id"]
            task_id_2 = response_2.json()["task_id"]
            assert task_id_1 != task_id_2

    # --- Invalid inputs ---

    def test_invalid_tier_returns_400(self, mock_tier_models):
        with patch("app.routes.models.TIER_MODELS", mock_tier_models):
            response = client.post("/models/setup", json={"tier": "ultra"})
            assert response.status_code == 400

    def test_invalid_tier_detail_mentions_value(self, mock_tier_models):
        with patch("app.routes.models.TIER_MODELS", mock_tier_models):
            response = client.post("/models/setup", json={"tier": "ultra"})
            json_response = response.json()
            detail = json_response["detail"]
            assert "ultra" in detail

    def test_missing_tier_returns_422(self):
        response = client.post("/models/setup", json={})
        assert response.status_code == 422

    def test_wrong_type_returns_422(self):
        response = client.post("/models/setup", json={"tier": 123})
        assert response.status_code == 422

    def test_empty_body_returns_422(self):
        response = client.post("/models/setup")
        assert response.status_code == 422


class TestStartDownloadModel:
    """Tests for POST /models/download/{model_key}"""

    # --- Status code tests ---

    def test_valid_model_key_returns_200(self, download_facenet_response):
        assert download_facenet_response.status_code == 200

    def test_unknown_model_key_returns_404(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry):
            response = client.post("/models/download/doesnotexist")
            assert response.status_code == 404

    def test_unknown_model_key_detail_mentions_key(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry):
            response = client.post("/models/download/doesnotexist")
            json_response = response.json()
            detail = json_response["detail"]
            assert "doesnotexist" in detail

    # --- Response structure ---

    def test_success_is_true(self, download_facenet_response):
        json_response = download_facenet_response.json()
        assert json_response["success"] is True

    def test_response_has_task_id(self, download_facenet_response):
        json_response = download_facenet_response.json()
        assert "task_id" in json_response

    def test_task_id_is_valid_uuid(self, download_facenet_response):
        json_response = download_facenet_response.json()
        task_id = json_response["task_id"]
        uuid.UUID(task_id)

    def test_response_has_message(self, download_facenet_response):
        json_response = download_facenet_response.json()
        assert "message" in json_response

    def test_message_contains_model_key(self, download_facenet_response):
        json_response = download_facenet_response.json()
        message = json_response["message"]
        assert "facenet" in message

    def test_each_call_gets_unique_task_id(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.ensure_model", return_value=None
        ):
            response_1 = client.post("/models/download/facenet")
            response_2 = client.post("/models/download/facenet")
            task_id_1 = response_1.json()["task_id"]
            task_id_2 = response_2.json()["task_id"]
            assert task_id_1 != task_id_2

    # --- All valid model keys ---

    @pytest.mark.parametrize(
        "model_key",
        [
            "yolo_nano",
            "yolo_nano_face",
            "yolo_small",
            "yolo_small_face",
            "yolo_medium",
            "yolo_medium_face",
            "facenet",
        ],
    )
    def test_all_valid_model_keys_return_200(self, model_key, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), patch(
            "app.routes.models.ensure_model", return_value=None
        ):
            response = client.post(f"/models/download/{model_key}")
            assert response.status_code == 200


# ##############################
# Test Classes — from upstream (verbatim)
# ##############################


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
