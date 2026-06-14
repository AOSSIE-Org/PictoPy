import sys
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes.models import router as models_router

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
            "feature": "object_detection",
            "tier": "nano",
            "size_mb": 10.2,
        },
        "yolo_nano_face": {
            "filename": "YOLOv11_Nano_Face.onnx",
            "feature": "face_detection",
            "tier": "nano",
            "size_mb": 10.1,
        },
        "yolo_small": {
            "filename": "YOLOv11_Small.onnx",
            "feature": "object_detection",
            "tier": "small",
            "size_mb": 36.2,
        },
        "yolo_small_face": {
            "filename": "YOLOv11_Small_Face.onnx",
            "feature": "face_detection",
            "tier": "small",
            "size_mb": 36.1,
        },
        "yolo_medium": {
            "filename": "YOLOv11_Medium.onnx",
            "feature": "object_detection",
            "tier": "medium",
            "size_mb": 76.9,
        },
        "yolo_medium_face": {
            "filename": "YOLOv11_Medium_Face.onnx",
            "feature": "face_detection",
            "tier": "medium",
            "size_mb": 76.6,
        },
        "facenet": {
            "filename": "FaceNet_128D.onnx",
            "feature": "face_embedding",
            "tier": "required",
            "size_mb": 87.0,
        },
    }
@pytest.fixture
def hardware_response():
    return client.get("/models/hardware")


# ##############################
# Test Classes
# ##############################

class TestModelStatus:
    """Tests suite for GET /models/status"""

    def test_returns_200(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.status_code == 200

    def test_success_is_true(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.json()["success"] is True

    def test_data_is_object(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert isinstance(response.json()["data"], dict)

    def test_all_7_models_present(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            data = response.json()["data"]
            expected = [
                "yolo_nano", "yolo_nano_face",
                "yolo_small", "yolo_small_face",
                "yolo_medium", "yolo_medium_face",
                "facenet",
            ]
            for key in expected:
                assert key in data, f"Missing model key: {key}"

    def test_each_model_has_required_fields(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert "name" in model
                assert "installed" in model
                assert "feature" in model
                assert "tier" in model
                assert "size_mb" in model

    def test_installed_is_always_boolean(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert isinstance(model["installed"], bool)

    def test_installed_true_when_file_exists(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=True):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["installed"] is True

    def test_installed_false_when_file_missing(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["installed"] is False

    def test_tier_values_are_valid(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            valid_tiers = ["nano", "small", "medium", "required"]
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert model["tier"] in valid_tiers

    def test_facenet_tier_is_required(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            assert response.json()["data"]["facenet"]["tier"] == "required"

    def test_size_mb_is_positive_number(self, mock_model_registry):
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            for model in response.json()["data"].values():
                assert isinstance(model["size_mb"], (int, float))
                assert model["size_mb"] > 0

    def test_name_field_matches_filename(self, mock_model_registry):
        # Route maps spec["filename"] → response field "name"
        # Verifying the mapping is correct
        with patch("app.routes.models.MODEL_REGISTRY", mock_model_registry), \
             patch("app.routes.models.get_model_path", return_value="/fake/path.onnx"), \
             patch("app.routes.models.os.path.exists", return_value=False):
            response = client.get("/models/status")
            data = response.json()["data"]
            assert data["facenet"]["name"] == "FaceNet_128D.onnx"
            assert data["yolo_nano"]["name"] == "YOLOv11_Nano.onnx"

class TestHardwareInformation:
    """Test suite for GET /models/hardware."""

    def test_returns_200(self, hardware_response):
        assert hardware_response.status_code == 200
    
    def test_returns_error_when_hardware_detection_fails(self):
        with patch(
            "app.routes.models.get_hardware_info",
            side_effect=Exception("hardware error")
        ):
            response = client.get("/models/hardware")

            assert response.status_code == 500

    def test_success_is_true(self, hardware_response):
        json_response = hardware_response.json()

        assert json_response["success"] is True
    
    def test_data_is_object(self, hardware_response):
        json_response = hardware_response.json()

        assert isinstance(json_response["data"], dict)

    def test_data_has_required_fields(self, hardware_response):
        json_response = hardware_response.json()
        data = json_response["data"]

        assert "ram_gb" in data
        assert "gpu_detected" in data
        assert "gpu_names" in data
        assert "apple_silicon" in data
        assert "available_providers" in data
        assert "recommended_tier" in data
    
    def test_ram_is_positive_number(self,hardware_response):
        json_response=hardware_response.json()
        ram=json_response["data"]["ram_gb"]
        
        assert isinstance(ram,(int,float)) 
        assert ram > 0
    
    def test_gpu_is_boolean(self,hardware_response):
        json_response=hardware_response.json()
        gpu_bool=json_response["data"]["gpu_detected"]

        assert isinstance(gpu_bool,bool)
    
    def test_gpu_names_is_array(self,hardware_response):
        json_response=hardware_response.json()
        gpu_names=json_response["data"]["gpu_names"]

        assert isinstance(gpu_names,list)
    
    def test_gpu_names_contains_strings(self, hardware_response):
        json_response = hardware_response.json()
        gpu_names = json_response["data"]["gpu_names"]

        for gpu in gpu_names:
            assert isinstance(gpu, str)
    
    def test_apple_silicon_type(self, hardware_response):
        json_response = hardware_response.json()
        apple_silicon = json_response["data"]["apple_silicon"]

        assert (
            apple_silicon is None
            or isinstance(apple_silicon, bool)
        )

    def test_no_gpu_returns_empty_gpu_names(self):
        mock_hw_info = {
            "ram_gb": 8.0,
            "gpu_detected": False,
            "gpu_names": [],
            "apple_silicon": None,
            "available_providers": ["CPUExecutionProvider"],
            "recommended_tier": "small",
        }

        with patch(
            "app.routes.models.get_hardware_info",
            return_value=mock_hw_info,
        ):
            response = client.get("/models/hardware")

            data = response.json()["data"]

            assert data["gpu_detected"] is False
            assert data["gpu_names"] == []

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
    
    def test_recommended_tier_is_valid(self,hardware_response):
        valid_tiers=["nano","small","medium"]
        json_response=hardware_response.json()
        recommended_tier=json_response["data"]["recommended_tier"]

        assert recommended_tier in valid_tiers
    
    def test_recommended_tier_is_string(self, hardware_response):
        json_response = hardware_response.json()    
        recommended_tiers=json_response["data"]["recommended_tier"]

        assert isinstance(recommended_tiers,str)


