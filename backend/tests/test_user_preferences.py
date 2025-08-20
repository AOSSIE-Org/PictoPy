import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.user_preferences import router as user_preferences_router

app = FastAPI()
app.include_router(user_preferences_router, prefix="/user_preferences")
client = TestClient(app)


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture
def sample_update_request():
    """Sample update user preferences request data."""
    return {"YOLO_model_size": "medium", "GPU_Acceleration": True}


@pytest.fixture
def sample_partial_update_request():
    """Sample partial update request data."""
    return {"YOLO_model_size": "medium"}


@pytest.fixture
def sample_metadata_with_preferences():
    """Sample metadata containing user preferences."""
    return {
        "user_preferences": {"YOLO_model_size": "small", "GPU_Acceleration": True},
        "other_metadata": "some_value",
    }


@pytest.fixture
def sample_metadata_without_preferences():
    """Sample metadata without user preferences."""
    return {"other_metadata": "some_value"}


@pytest.fixture
def empty_metadata():
    """Empty metadata."""
    return {}


# ##############################
# Test Classes
# ##############################


class TestUserPreferencesAPI:
    """Test class for User Preferences API endpoints."""

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_with_existing_data(
        self, mock_get_metadata, sample_metadata_with_preferences
    ):
        """Test successful retrieval of user preferences when data exists."""

        mock_get_metadata.return_value = sample_metadata_with_preferences

        response = client.get("/user_preferences/")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["success"] is True
        assert response_data["message"] == "Successfully retrieved user preferences"

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "small"
        assert user_prefs["GPU_Acceleration"] is True

        mock_get_metadata.assert_called_once()

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_with_defaults(
        self, mock_get_metadata, sample_metadata_without_preferences
    ):
        """Test retrieval of user preferences with default values when no preferences exist."""

        mock_get_metadata.return_value = sample_metadata_without_preferences

        response = client.get("/user_preferences/")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["success"] is True
        assert response_data["message"] == "Successfully retrieved user preferences"

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "small"
        assert user_prefs["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_empty_metadata(self, mock_get_metadata):
        """Test retrieval when metadata is empty."""

        mock_get_metadata.return_value = {}

        response = client.get("/user_preferences/")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["success"] is True
        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "small"
        assert user_prefs["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_null_metadata(self, mock_get_metadata):
        """Test retrieval when metadata is None."""

        mock_get_metadata.return_value = None

        response = client.get("/user_preferences/")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["success"] is True
        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "small"
        assert user_prefs["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_partial_data(self, mock_get_metadata):
        """Test retrieval when only some preference fields exist."""

        mock_get_metadata.return_value = {
            "user_preferences": {"YOLO_model_size": "medium"}
        }

        response = client.get("/user_preferences/")

        assert response.status_code == 200
        response_data = response.json()

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "medium"
        assert user_prefs["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_get_user_preferences_database_exception(self, mock_get_metadata):
        """Test get user preferences when database raises an exception."""

        mock_get_metadata.side_effect = Exception("Database connection error")

        response = client.get("/user_preferences/")

        assert response.status_code == 500
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Internal server error"
            assert "Database connection error" in response_data["detail"]["message"]
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Internal server error"
            assert "Database connection error" in response_data["message"]

    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_full_update(
        self,
        mock_get_metadata,
        mock_update_metadata,
        sample_metadata_with_preferences,
        sample_update_request,
    ):
        """Test successful full update of user preferences."""

        mock_get_metadata.return_value = sample_metadata_with_preferences
        mock_update_metadata.return_value = True

        response = client.put("/user_preferences/", json=sample_update_request)

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["success"] is True
        assert response_data["message"] == "Successfully updated user preferences"

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "medium"
        assert user_prefs["GPU_Acceleration"] is True

        mock_get_metadata.assert_called_once()
        mock_update_metadata.assert_called_once()

        updated_metadata = mock_update_metadata.call_args[0][0]
        assert updated_metadata["user_preferences"]["YOLO_model_size"] == "medium"
        assert updated_metadata["user_preferences"]["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_partial_update(
        self, mock_get_metadata, mock_update_metadata, sample_metadata_with_preferences
    ):
        """Test successful partial update of user preferences."""

        mock_get_metadata.return_value = sample_metadata_with_preferences
        mock_update_metadata.return_value = True

        partial_request = {"YOLO_model_size": "medium"}

        response = client.put("/user_preferences/", json=partial_request)

        assert response.status_code == 200
        response_data = response.json()

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "medium"
        assert user_prefs["GPU_Acceleration"] is True

    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_new_metadata(
        self, mock_get_metadata, mock_update_metadata
    ):
        """Test update when no existing metadata exists."""

        mock_get_metadata.return_value = None
        mock_update_metadata.return_value = True

        request_data = {"YOLO_model_size": "medium", "GPU_Acceleration": False}

        response = client.put("/user_preferences/", json=request_data)

        assert response.status_code == 200
        response_data = response.json()

        user_prefs = response_data["user_preferences"]
        assert user_prefs["YOLO_model_size"] == "medium"
        assert user_prefs["GPU_Acceleration"] is False

    @pytest.mark.parametrize(
        "yolo_size,gpu_accel",
        [
            ("small", True),
            ("medium", False),
            ("nano", True),
            (None, False),
            ("medium", None),
        ],
    )
    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_various_combinations(
        self, mock_get_metadata, mock_update_metadata, yolo_size, gpu_accel
    ):
        """Test update with various parameter combinations."""

        mock_get_metadata.return_value = {}
        mock_update_metadata.return_value = True

        request_data = {}
        if yolo_size is not None:
            request_data["YOLO_model_size"] = yolo_size
        if gpu_accel is not None:
            request_data["GPU_Acceleration"] = gpu_accel

        response = client.put("/user_preferences/", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True

    def test_update_user_preferences_no_fields_provided(self):
        """Test update with no fields provided."""
        response = client.put("/user_preferences/", json={})

        assert response.status_code == 400
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Validation Error"
            assert (
                "At least one preference field must be provided"
                in response_data["detail"]["message"]
            )
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Validation Error"
            assert (
                "At least one preference field must be provided"
                in response_data["message"]
            )

    def test_update_user_preferences_all_none_fields(self):
        """Test update with all fields explicitly set to None."""
        response = client.put(
            "/user_preferences/",
            json={"YOLO_model_size": None, "GPU_Acceleration": None},
        )

        assert response.status_code == 400
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Validation Error"
            assert (
                "At least one preference field must be provided"
                in response_data["detail"]["message"]
            )
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Validation Error"
            assert (
                "At least one preference field must be provided"
                in response_data["message"]
            )

    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_database_update_failed(
        self, mock_get_metadata, mock_update_metadata
    ):
        """Test update when database update fails."""

        mock_get_metadata.return_value = {}
        mock_update_metadata.return_value = False

        response = client.put("/user_preferences/", json={"YOLO_model_size": "medium"})

        assert response.status_code == 500
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Update Failed"
            assert (
                "Failed to update user preferences"
                in response_data["detail"]["message"]
            )
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Update Failed"
            assert "Failed to update user preferences" in response_data["message"]

    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_database_get_exception(self, mock_get_metadata):
        """Test update when database get raises an exception."""

        mock_get_metadata.side_effect = Exception("Database connection error")

        response = client.put("/user_preferences/", json={"YOLO_model_size": "medium"})

        assert response.status_code == 500
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Internal server error"
            assert "Database connection error" in response_data["detail"]["message"]
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Internal server error"
            assert "Database connection error" in response_data["message"]

    @patch("app.routes.user_preferences.db_update_metadata")
    @patch("app.routes.user_preferences.db_get_metadata")
    def test_update_user_preferences_database_update_exception(
        self, mock_get_metadata, mock_update_metadata
    ):
        """Test update when database update raises an exception."""

        mock_get_metadata.return_value = {}
        mock_update_metadata.side_effect = Exception("Database update error")

        response = client.put("/user_preferences/", json={"YOLO_model_size": "medium"})

        assert response.status_code == 500
        response_data = response.json()

        if "detail" in response_data:
            assert response_data["detail"]["success"] is False
            assert response_data["detail"]["error"] == "Internal server error"
            assert "Database update error" in response_data["detail"]["message"]
        else:
            assert response_data["success"] is False
            assert response_data["error"] == "Internal server error"
            assert "Database update error" in response_data["message"]

    def test_get_user_preferences_response_structure(self):
        """Test that get user preferences returns correct response structure."""
        with patch("app.routes.user_preferences.db_get_metadata") as mock_get:
            mock_get.return_value = {}

            response = client.get("/user_preferences/")
            response_data = response.json()

            required_fields = ["success", "message", "user_preferences"]
            for field in required_fields:
                assert field in response_data

            user_prefs = response_data["user_preferences"]
            prefs_fields = ["YOLO_model_size", "GPU_Acceleration"]
            for field in prefs_fields:
                assert field in user_prefs

            assert isinstance(user_prefs["YOLO_model_size"], str)
            assert isinstance(user_prefs["GPU_Acceleration"], bool)

    def test_update_user_preferences_response_structure(self):
        """Test that update user preferences returns correct response structure."""
        with patch("app.routes.user_preferences.db_get_metadata") as mock_get, patch(
            "app.routes.user_preferences.db_update_metadata"
        ) as mock_update:

            mock_get.return_value = {}
            mock_update.return_value = True

            response = client.put(
                "/user_preferences/", json={"YOLO_model_size": "medium"}
            )

            assert response.status_code == 200
            response_data = response.json()

            required_fields = ["success", "message", "user_preferences"]
            for field in required_fields:
                assert field in response_data

            user_prefs = response_data["user_preferences"]
            prefs_fields = ["YOLO_model_size", "GPU_Acceleration"]
            for field in prefs_fields:
                assert field in user_prefs

    def test_update_user_preferences_preserves_other_metadata(self):
        """Test that updating preferences preserves other metadata fields."""
        with patch("app.routes.user_preferences.db_get_metadata") as mock_get, patch(
            "app.routes.user_preferences.db_update_metadata"
        ) as mock_update:

            existing_metadata = {
                "user_preferences": {"YOLO_model_size": "small"},
                "other_field": "should_be_preserved",
                "another_field": {"nested": "data"},
            }
            mock_get.return_value = existing_metadata
            mock_update.return_value = True

            response = client.put("/user_preferences/", json={"GPU_Acceleration": True})

            assert response.status_code == 200

            updated_metadata = mock_update.call_args[0][0]
            assert updated_metadata["other_field"] == "should_be_preserved"
            assert updated_metadata["another_field"]["nested"] == "data"
            assert updated_metadata["user_preferences"]["GPU_Acceleration"] is True

    def test_update_user_preferences_missing_request_body(self):
        """Test update with missing request body."""
        response = client.put("/user_preferences/")

        assert response.status_code == 422

    def test_update_user_preferences_invalid_yolo_size(self):
        """Test update with invalid YOLO model size."""
        response = client.put(
            "/user_preferences/", json={"YOLO_model_size": "invalid_size"}
        )

        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data

    def test_update_user_preferences_invalid_json_structure(self):
        """Test update with invalid JSON structure (no valid fields)."""
        response = client.put("/user_preferences/", json={"invalid_field": "value"})

        """Should return 400 for invalid request structure."""
        assert response.status_code == 400
        response_data = response.json()

        if "detail" in response_data:
            assert (
                "At least one preference field must be provided"
                in response_data["detail"]["message"]
            )
        else:
            assert (
                "At least one preference field must be provided"
                in response_data["message"]
            )

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("DELETE", "/user_preferences/"),
            ("POST", "/user_preferences/"),
            ("PATCH", "/user_preferences/"),
        ],
    )
    def test_unsupported_http_methods(self, method, endpoint):
        """Test that unsupported HTTP methods return 405."""
        response = client.request(method, endpoint)
        assert response.status_code == 405
