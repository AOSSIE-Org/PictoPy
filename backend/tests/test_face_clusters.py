import pytest
from unittest.mock import patch, MagicMock
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
    return {
        "cluster_name": "John Doe"
    }


@pytest.fixture
def sample_cluster_data():
    """Sample cluster data from database."""
    return {
        "cluster_id": "cluster_123",
        "cluster_name": "Original Name",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_clusters_with_counts():
    """Sample clusters data with face counts."""
    return [
        {
            "cluster_id": "cluster_1",
            "cluster_name": "John Doe",
            "face_count": 15
        },
        {
            "cluster_id": "cluster_2", 
            "cluster_name": "Jane Smith",
            "face_count": 8
        },
        {
            "cluster_id": "cluster_3",
            "cluster_name": "Unknown Person",
            "face_count": 3
        }
    ]


# ##############################
# Test Classes
# ##############################


class TestFaceClustersAPI:
    """Test class for Face Clusters API endpoints."""

    @pytest.mark.parametrize("cluster_id,cluster_name", [
        ("cluster_123", "John Doe"),
        ("cluster_456", "Jane Smith"),
        ("cluster_789", "Bob Johnson"),
    ])
    @patch("app.routes.face_clusters.db_update_cluster")
    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_success(
        self, 
        mock_get_cluster, 
        mock_update_cluster, 
        cluster_id, 
        cluster_name,
        sample_cluster_data
    ):
        """Test successful cluster rename."""
        mock_get_cluster.return_value = sample_cluster_data
        mock_update_cluster.return_value = True

        response = client.put(
            f"/face_clusters/{cluster_id}",
            json={"cluster_name": cluster_name}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["success"] is True
        assert response_data["cluster_id"] == cluster_id
        assert response_data["cluster_name"] == cluster_name
        assert f"Successfully renamed cluster to '{cluster_name}'" in response_data["message"]
        
        mock_get_cluster.assert_called_once_with(cluster_id)
        mock_update_cluster.assert_called_once_with(
            cluster_id=cluster_id,
            cluster_name=cluster_name
        )

    @patch("app.routes.face_clusters.db_get_cluster_by_id")
    def test_rename_cluster_not_found(self, mock_get_cluster):
        """Test rename cluster when cluster doesn't exist."""
        mock_get_cluster.return_value = None
        
        response = client.put(
            "/face_clusters/nonexistent_cluster",
            json={"cluster_name": "New Name"}
        )
        
        response_data = response.json()

        assert response.status_code == 404
        assert response_data["detail"]["success"] is False
        assert response_data["detail"]["error"] == "Cluster Not Found"
        assert "nonexistent_cluster" in response_data["detail"]["message"]

    @pytest.mark.parametrize("invalid_cluster_id", [""])
    def test_rename_cluster_invalid_path(self, invalid_cluster_id):
        """Test rename cluster with invalid (empty) path param which results in 405."""
        response = client.put(
            f"/face_clusters/{invalid_cluster_id}",
            json={"cluster_name": "Valid Name"}
        )

        assert response.status_code == 405

    def test_rename_cluster_name_whitespace_trimming(self, sample_cluster_data):
        """Test that cluster names are properly trimmed of whitespace."""
        with patch("app.routes.face_clusters.db_get_cluster_by_id") as mock_get, \
            patch("app.routes.face_clusters.db_update_cluster") as mock_update:
            mock_get.return_value = sample_cluster_data
            mock_update.return_value = True
            
            response = client.put(
                "/face_clusters/cluster_123",
                json={"cluster_name": "  John Doe  "}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert response_data["cluster_name"] == "John Doe"  # Trimmed
            mock_update.assert_called_once_with(
                cluster_id="cluster_123",
                cluster_name="John Doe"  # Should be trimmed
            )

    @patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts")
    def test_get_all_clusters_success(self, mock_get_clusters, sample_clusters_with_counts):
        """Test successful retrieval of all clusters."""
        mock_get_clusters.return_value = sample_clusters_with_counts
        
        response = client.get("/face_clusters/")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["success"] is True
        assert "Successfully retrieved 3 cluster(s)" in response_data["message"]
        assert len(response_data["clusters"]) == 3
        
        first_cluster = response_data["clusters"][0]
        assert "cluster_id" in first_cluster
        assert "cluster_name" in first_cluster
        assert "face_count" in first_cluster
        
        assert first_cluster["cluster_id"] == "cluster_1"
        assert first_cluster["cluster_name"] == "John Doe"
        assert first_cluster["face_count"] == 15

    @patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts")
    def test_get_all_clusters_empty_result(self, mock_get_clusters):
        """Test get all clusters when no clusters exist."""
        mock_get_clusters.return_value = []
        
        response = client.get("/face_clusters/")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["success"] is True
        assert "Successfully retrieved 0 cluster(s)" in response_data["message"]
        assert response_data["clusters"] == []

    def test_get_all_clusters_response_structure(self, sample_clusters_with_counts):
        """Test that get all clusters returns correct response structure."""
        with patch("app.routes.face_clusters.db_get_all_clusters_with_face_counts") as mock_get:
            mock_get.return_value = sample_clusters_with_counts
            
            response = client.get("/face_clusters/")
            response_data = response.json()
            
            required_fields = ["success", "message", "clusters"]
            for field in required_fields:
                assert field in response_data
            
            for cluster in response_data["clusters"]:
                cluster_fields = ["cluster_id", "cluster_name", "face_count"]
                for field in cluster_fields:
                    assert field in cluster
                    
                assert isinstance(cluster["cluster_id"], str)
                assert isinstance(cluster["cluster_name"], str)
                assert isinstance(cluster["face_count"], int)

    def test_rename_cluster_missing_request_body(self):
        """Test rename cluster with missing request body."""
        response = client.put("/face_clusters/cluster_123")
        
        assert response.status_code == 422

    def test_rename_cluster_invalid_json(self):
        """Test rename cluster with invalid JSON structure."""
        response = client.put(
            "/face_clusters/cluster_123",
            json={"invalid_field": "value"}
        )
        
        assert response.status_code == 422

    @pytest.mark.parametrize("method,endpoint", [
        ("DELETE", "/face_clusters/cluster_123"),
        ("POST", "/face_clusters/cluster_123"),
        ("PATCH", "/face_clusters/cluster_123"),
        ("DELETE", "/face_clusters/"),
        ("POST", "/face_clusters/"),
        ("PUT", "/face_clusters/"),
    ])
    def test_unsupported_http_methods(self, method, endpoint):
        """Test that unsupported HTTP methods return 405."""
        response = client.request(method, endpoint)
        assert response.status_code == 405
