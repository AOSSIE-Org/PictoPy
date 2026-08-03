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
        with (
            patch("app.routes.user_preferences.db_get_metadata") as mock_get,
            patch("app.routes.user_preferences.db_update_metadata") as mock_update,
        ):
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
        with (
            patch("app.routes.user_preferences.db_get_metadata") as mock_get,
            patch("app.routes.user_preferences.db_update_metadata") as mock_update,
        ):
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


class TestVideoFrameIntervalValidation:
    """Boundary coverage for the video keyframe interval on both preference
    models, guarding the sampling API contract."""

    def test_default_matches_sampler_config(self):
        from app.schemas.user_preferences import UserPreferencesData
        from app.config.settings import VIDEO_FRAME_INTERVAL_SECONDS

        assert (
            UserPreferencesData().Video_Frame_Interval == VIDEO_FRAME_INTERVAL_SECONDS
        )

    @pytest.mark.parametrize(
        "value",
        [
            0.5,  # exact minimum
            300.0,  # exact maximum
            5.0,
        ],
    )
    def test_accepts_in_range_values(self, value):
        from app.schemas.user_preferences import (
            UserPreferencesData,
            UpdateUserPreferencesRequest,
        )

        assert UserPreferencesData(Video_Frame_Interval=value).Video_Frame_Interval == (
            value
        )
        assert (
            UpdateUserPreferencesRequest(
                Video_Frame_Interval=value
            ).Video_Frame_Interval
            == value
        )

    @pytest.mark.parametrize("value", [0.4, 300.1, 0.0, -1.0])
    def test_rejects_out_of_range_values(self, value):
        from pydantic import ValidationError
        from app.schemas.user_preferences import (
            UserPreferencesData,
            UpdateUserPreferencesRequest,
        )

        with pytest.raises(ValidationError):
            UserPreferencesData(Video_Frame_Interval=value)
        with pytest.raises(ValidationError):
            UpdateUserPreferencesRequest(Video_Frame_Interval=value)

    def test_partial_update_allows_none(self):
        from app.schemas.user_preferences import UpdateUserPreferencesRequest

        assert UpdateUserPreferencesRequest().Video_Frame_Interval is None
        assert (
            UpdateUserPreferencesRequest(Video_Frame_Interval=None).Video_Frame_Interval
            is None
        )


# ##############################
# Memories preferences
# ##############################


class TestMemoriesPreferences:
    def test_defaults_appear_when_the_key_is_absent(self):
        with patch(
            "app.routes.user_preferences.db_get_metadata",
            return_value={"user_preferences": {"YOLO_model_size": "small"}},
        ):
            response = client.get("/user_preferences/")

        memories = response.json()["user_preferences"]["memories"]
        assert memories["enabled"] is True
        # Desktop alerts are opt-in.
        assert memories["notifications_enabled"] is False
        # The story viewer ships muted; audio is opt-in.
        assert memories["story_music_enabled"] is False
        assert memories["min_images"] == 5
        assert memories["max_images"] == 30

    def test_stored_values_round_trip(self):
        stored = {
            "user_preferences": {
                "memories": {"story_music_enabled": True, "min_images": 8}
            }
        }
        with patch("app.routes.user_preferences.db_get_metadata", return_value=stored):
            memories = client.get("/user_preferences/").json()["user_preferences"][
                "memories"
            ]

        assert memories["story_music_enabled"] is True
        assert memories["min_images"] == 8
        assert memories["max_images"] == 30  # untouched default

    def test_partial_update_preserves_sibling_fields(self):
        stored = {
            "user_preferences": {
                "YOLO_model_size": "medium",
                "memories": {"enabled": False, "min_images": 7},
            }
        }
        with (
            patch("app.routes.user_preferences.db_get_metadata", return_value=stored),
            patch(
                "app.routes.user_preferences.db_update_metadata", return_value=True
            ) as update,
        ):
            response = client.put(
                "/user_preferences/", json={"memories": {"story_music_enabled": True}}
            )

        assert response.status_code == 200
        saved = update.call_args[0][0]["user_preferences"]
        assert saved["YOLO_model_size"] == "medium"
        assert saved["memories"] == {
            "enabled": False,
            "min_images": 7,
            "story_music_enabled": True,
        }

    def test_updating_only_memories_is_a_valid_request(self):
        with (
            patch("app.routes.user_preferences.db_get_metadata", return_value={}),
            patch("app.routes.user_preferences.db_update_metadata", return_value=True),
        ):
            response = client.put(
                "/user_preferences/", json={"memories": {"enabled": False}}
            )

        assert response.status_code == 200
        assert response.json()["user_preferences"]["memories"]["enabled"] is False

    def test_weights_normalize_to_one_on_read(self):
        stored = {
            "user_preferences": {
                "memories": {
                    "weights": {
                        "favourite": 1.0,
                        "known_people": 0.5,
                        "event_strength": 0.5,
                        "face_presence": 0.4,
                        "semantic_confidence": 0.0,
                        "gps_novelty": 0.0,
                        "in_album": 0.0,
                    }
                }
            }
        }
        with patch("app.routes.user_preferences.db_get_metadata", return_value=stored):
            weights = client.get("/user_preferences/").json()["user_preferences"][
                "memories"
            ]["weights"]

        assert round(sum(weights.values()), 6) == 1.0
        assert weights["favourite"] > weights["known_people"]

    def test_partial_weights_are_stored_raw_not_rescaled(self):
        """Rescaling a lone slider to 1.0 would silently zero out the others."""
        stored = {"user_preferences": {"memories": {"weights": {"known_people": 0.4}}}}
        with (
            patch("app.routes.user_preferences.db_get_metadata", return_value=stored),
            patch(
                "app.routes.user_preferences.db_update_metadata", return_value=True
            ) as update,
        ):
            client.put(
                "/user_preferences/", json={"memories": {"weights": {"favourite": 0.6}}}
            )

        saved = update.call_args[0][0]["user_preferences"]["memories"]["weights"]
        assert saved == {"known_people": 0.4, "favourite": 0.6}

    def test_all_zero_weights_fall_back_to_defaults(self):
        from app.schemas.user_preferences import MemoryScoringWeights

        zeroed = MemoryScoringWeights(
            **{name: 0.0 for name in MemoryScoringWeights.model_fields}
        )
        assert zeroed.favourite == 0.22

    @pytest.mark.parametrize(
        "payload",
        [
            {"memories": {"min_images": 1}},
            {"memories": {"min_images": 99}},
            {"memories": {"max_images": 1}},
            {"memories": {"weights": {"favourite": -0.1}}},
            {"memories": {"weights": {"favourite": 1.5}}},
        ],
    )
    def test_rejects_out_of_range_values(self, payload):
        assert client.put("/user_preferences/", json=payload).status_code == 422

    def test_rejects_max_images_below_min_images(self):
        with (
            patch("app.routes.user_preferences.db_get_metadata", return_value={}),
            patch("app.routes.user_preferences.db_update_metadata", return_value=True),
        ):
            response = client.put(
                "/user_preferences/",
                json={"memories": {"min_images": 40, "max_images": 10}},
            )

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "Validation Error"

    def test_bounds_are_checked_against_the_merged_result(self):
        """max_images lives in storage; a min_images-only patch can still break it."""
        stored = {"user_preferences": {"memories": {"max_images": 10}}}
        with (
            patch("app.routes.user_preferences.db_get_metadata", return_value=stored),
            patch("app.routes.user_preferences.db_update_metadata", return_value=True),
        ):
            response = client.put(
                "/user_preferences/", json={"memories": {"min_images": 40}}
            )

        assert response.status_code == 400

    def test_corrupt_stored_preferences_fall_back_to_defaults(self):
        with patch(
            "app.routes.user_preferences.db_get_metadata",
            return_value={"user_preferences": {"YOLO_model_size": "gigantic"}},
        ):
            response = client.get("/user_preferences/")

        assert response.status_code == 200
        assert response.json()["user_preferences"]["YOLO_model_size"] == "small"
