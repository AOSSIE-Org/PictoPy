import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.face_clusters import router as face_clusters_router


app = FastAPI()
app.include_router(face_clusters_router, prefix="/face_clusters")
client = TestClient(app)


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture
def sample_rename_request():
    """Sample rename cluster request data."""
    return {"cluster_name": "John Doe"}


@pytest.fixture
def sample_cluster_data():
    """Sample cluster data from database."""
    return {
        "cluster_id": "cluster_123",
        "cluster_name": "Original Name",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_clusters_with_counts():
    """Sample clusters data with face counts."""
    return [
        {
            "cluster_id": "cluster_1",
            "cluster_name": "John Doe",
            "face_count": 15,
            "face_image_base64": "base64_string_1",
        },
        {
            "cluster_id": "cluster_2",
            "cluster_name": "Jane Smith",
            "face_count": 8,
            "face_image_base64": "base64_string_2",
        },
        {
            "cluster_id": "cluster_3",
            "cluster_name": "Unknown Person",
            "face_count": 3,
            "face_image_base64": "base64_string_3",
        },
    ]


@pytest.fixture
def sample_cluster_images():
    """Sample images data for a cluster."""
    return [
        {
            "image_id": "img_1",
            "image_path": "/path/to/image1.jpg",
            "thumbnail_path": "/path/to/thumb1.jpg",
            "metadata": {"camera": "Canon"},
            "face_id": 101,
            "confidence": 0.95,
            "bbox": {"x": 100, "y": 200, "width": 150, "height": 200},
        },
        {
            "image_id": "img_2",
            "image_path": "/path/to/image2.jpg",
            "thumbnail_path": "/path/to/thumb2.jpg",
            "metadata": {"camera": "Nikon"},
            "face_id": 102,
            "confidence": 0.87,
            "bbox": {"x": 50, "y": 100, "width": 120, "height": 160},
        },
    ]


# ##############################
# Test Classes
# ##############################


class TestFaceClustersAPI:
    """Test class for Face Clusters API endpoints."""

    # ============================================================================
    # PUT /face_clusters/{cluster_id} - Rename Cluster Tests
    # ============================================================================

    @patch("app.routes.face_clusters.db_update_cluster")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_success(
        self, mock_get_cluster, mock_update_cluster, sample_rename_request
    ):
        """Test successfully renaming a cluster."""
        cluster_id = "cluster_123"
        mock_get_cluster.return_value = {
            "cluster_id": cluster_id,
            "cluster_name": "Old Name",
        }
        mock_update_cluster.return_value = True

        response = client.put(
            f"/face_clusters/{cluster_id}", json=sample_rename_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully renamed cluster" in data["message"]
        assert data["data"]["cluster_id"] == cluster_id
        assert data["data"]["cluster_name"] == sample_rename_request["cluster_name"]

        mock_get_cluster.assert_called_once_with(cluster_id)
        mock_update_cluster.assert_called_once_with(
            cluster_id=cluster_id, cluster_name=sample_rename_request["cluster_name"]
        )

    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_not_found(self, mock_get_cluster):
        """Test renaming a cluster that doesn't exist."""
        cluster_id = "non_existent_cluster"
        mock_get_cluster.return_value = None

        request_data = {"cluster_name": "New Name"}
        response = client.put(f"/face_clusters/{cluster_id}", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Cluster Not Found"

    def test_rename_cluster_empty_name(self):
        """Test renaming cluster with empty name."""
        cluster_id = "cluster_123"
        request_data = {"cluster_name": "   "}

        response = client.put(f"/face_clusters/{cluster_id}", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "Cluster name cannot be empty" in data["detail"]["message"]

    def test_rename_cluster_empty_id(self):
        """Test renaming cluster with empty ID."""
        cluster_id = "   "
        request_data = {"cluster_name": "Valid Name"}

        response = client.put(f"/face_clusters/{cluster_id}", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "Cluster ID cannot be empty" in data["detail"]["message"]

    @patch("app.routes.face_clusters.db_update_cluster")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_update_failed(self, mock_get_cluster, mock_update_cluster):
        """Test renaming cluster when database update fails."""
        cluster_id = "cluster_123"
        mock_get_cluster.return_value = {
            "cluster_id": cluster_id,
            "cluster_name": "Old Name",
        }
        mock_update_cluster.return_value = False

        request_data = {"cluster_name": "New Name"}
        response = client.put(f"/face_clusters/{cluster_id}", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Update Failed"

    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_database_error(self, mock_get_cluster):
        """Test renaming cluster when database raises an exception."""
        cluster_id = "cluster_123"
        mock_get_cluster.side_effect = Exception("Database connection failed")

        request_data = {"cluster_name": "New Name"}
        response = client.put(f"/face_clusters/{cluster_id}", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    @patch("app.routes.face_clusters.db_update_cluster")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_name_whitespace_trimming(
        self, mock_get_cluster, mock_update_cluster, sample_cluster_data
    ):
        """Test that cluster names are properly trimmed of whitespace."""
        mock_get_cluster.return_value = sample_cluster_data
        mock_update_cluster.return_value = True

        response = client.put(
            "/face_clusters/cluster_123", json={"cluster_name": "  John Doe  "}
        )

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["data"]["cluster_name"] == "John Doe"  # Trimmed
        mock_update_cluster.assert_called_once_with(
            cluster_id="cluster_123",
            cluster_name="John Doe",  # Should be trimmed
        )

    # ============================================================================
    # GET /face_clusters/ - Get All Clusters Tests
    # ============================================================================

    @patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts")
    def test_get_all_clusters_success(
        self, mock_get_clusters, sample_clusters_with_counts
    ):
        """Test successfully retrieving all clusters."""
        mock_get_clusters.return_value = sample_clusters_with_counts

        response = client.get("/face_clusters/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 3 cluster(s)" in data["message"]
        assert len(data["data"]["clusters"]) == 3

        # Check first cluster details
        first_cluster = data["data"]["clusters"][0]
        assert first_cluster["cluster_id"] == "cluster_1"
        assert first_cluster["cluster_name"] == "John Doe"
        assert first_cluster["face_count"] == 15
        assert first_cluster["face_image_base64"] == "base64_string_1"

        mock_get_clusters.assert_called_once()

    @patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts")
    def test_get_all_clusters_empty(self, mock_get_clusters):
        """Test retrieving clusters when none exist."""
        mock_get_clusters.return_value = []

        response = client.get("/face_clusters/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 0 cluster(s)" in data["message"]
        assert data["data"]["clusters"] == []

    @patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts")
    def test_get_all_clusters_database_error(self, mock_get_clusters):
        """Test handling database errors during cluster retrieval."""
        mock_get_clusters.side_effect = Exception("Database connection failed")

        response = client.get("/face_clusters/")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    def test_get_all_clusters_response_structure(self, sample_clusters_with_counts):
        """Test that get all clusters returns correct response structure."""
        with patch(
            "app.routes.face_clusters.db_get_all_clusters_with_face_counts"
        ) as mock_get:
            mock_get.return_value = sample_clusters_with_counts

            response = client.get("/face_clusters/")
            response_data = response.json()

            required_fields = ["success", "message", "data"]
            for field in required_fields:
                assert field in response_data

            assert "clusters" in response_data["data"]
            for cluster in response_data["data"]["clusters"]:
                cluster_fields = ["cluster_id", "cluster_name", "face_count"]
                for field in cluster_fields:
                    assert field in cluster

                assert isinstance(cluster["cluster_id"], str)
                assert isinstance(cluster["cluster_name"], str)
                assert isinstance(cluster["face_count"], int)

    # ============================================================================
    # GET /face_clusters/{cluster_id}/images - Get Cluster Images Tests
    # ============================================================================

    @patch("app.routes.face_clusters.db_get_images_by_cluster_id")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_get_cluster_images_success(
        self, mock_get_cluster, mock_get_images, sample_cluster_images
    ):
        """Test successfully retrieving images for a cluster."""
        cluster_id = "cluster_123"
        mock_get_cluster.return_value = {
            "cluster_id": cluster_id,
            "cluster_name": "John Doe",
        }
        mock_get_images.return_value = sample_cluster_images

        response = client.get(f"/face_clusters/{cluster_id}/images")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 2 image(s)" in data["message"]
        assert data["data"]["cluster_id"] == cluster_id
        assert data["data"]["cluster_name"] == "John Doe"
        assert data["data"]["total_images"] == 2
        assert len(data["data"]["images"]) == 2

        # Check first image details
        first_image = data["data"]["images"][0]
        assert first_image["id"] == "img_1"
        assert first_image["path"] == "/path/to/image1.jpg"
        assert first_image["face_id"] == 101
        assert first_image["confidence"] == 0.95

        mock_get_cluster.assert_called_once_with(cluster_id)
        mock_get_images.assert_called_once_with(cluster_id)

    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_get_cluster_images_cluster_not_found(self, mock_get_cluster):
        """Test getting images for a cluster that doesn't exist."""
        cluster_id = "non_existent_cluster"
        mock_get_cluster.return_value = None

        response = client.get(f"/face_clusters/{cluster_id}/images")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Cluster Not Found"

    @patch("app.routes.face_clusters.db_get_images_by_cluster_id")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_get_cluster_images_empty(self, mock_get_cluster, mock_get_images):
        """Test getting images for a cluster with no images."""
        cluster_id = "cluster_123"
        mock_get_cluster.return_value = {
            "cluster_id": cluster_id,
            "cluster_name": "Empty Cluster",
        }
        mock_get_images.return_value = []

        response = client.get(f"/face_clusters/{cluster_id}/images")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 0 image(s)" in data["message"]
        assert data["data"]["total_images"] == 0
        assert data["data"]["images"] == []

    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_get_cluster_images_database_error(self, mock_get_cluster):
        """Test handling database errors during image retrieval."""
        cluster_id = "cluster_123"
        mock_get_cluster.side_effect = Exception("Database connection failed")

        response = client.get(f"/face_clusters/{cluster_id}/images")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    # ============================================================================
    # Additional Edge Case Tests
    # ============================================================================

    def test_rename_cluster_missing_request_body(self):
        """Test rename cluster with missing request body."""
        response = client.put("/face_clusters/cluster_123")

        assert response.status_code == 422

    def test_rename_cluster_invalid_json(self):
        """Test rename cluster with invalid JSON structure."""
        response = client.put(
            "/face_clusters/cluster_123", json={"invalid_field": "value"}
        )

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("DELETE", "/face_clusters/cluster_123"),
            ("POST", "/face_clusters/cluster_123"),
            ("PATCH", "/face_clusters/cluster_123"),
            ("DELETE", "/face_clusters/"),
            ("POST", "/face_clusters/"),
            ("PUT", "/face_clusters/"),
        ],
    )
    def test_unsupported_http_methods(self, method, endpoint):
        """Test that unsupported HTTP methods return 405."""
        response = client.request(method, endpoint)
        assert response.status_code == 405
