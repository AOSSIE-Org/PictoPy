import pytest
import numpy as np
from unittest.mock import patch
from fastapi import FastAPI
import app.database.face_clusters as face_clusters_db
import app.database.faces as faces_db
import app.database.images as images_db
import app.database.folders as folders_db
import app.database.yolo_mapping as yolo_db
from app.utils.face_clusters import (
    cluster_util_cluster_all_face_embeddings,
    cluster_util_face_clusters_sync,
    cluster_util_is_reclustering_needed,
    estimate_eps,
)
from app.utils.face_quality import face_passes_quality_gate
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


# ============================================================================
# Algorithmic Logic Tests
# ============================================================================


def generate_synthetic_embeddings(
    num_identities=2, points_per_identity=10, dim=512, noise_std=0.005
):
    """Helper to generate tight clusters of embeddings."""
    embeddings = []
    labels = []

    np.random.seed(42)  # For reproducibility

    for i in range(num_identities):
        # Random unit vector as center
        center = np.random.randn(dim)
        center = center / np.linalg.norm(center)

        # Add points around center
        for _ in range(points_per_identity):
            noise = np.random.randn(dim) * noise_std
            point = center + noise
            # Re-normalize as cosine distance works best with unit vectors
            point = point / np.linalg.norm(point)
            embeddings.append(point)
            labels.append(i)

    return np.array(embeddings), np.array(labels)


def generate_noise_embeddings(num_points=80, dim=512):
    """Helper to generate random noise embeddings."""
    np.random.seed(43)
    noise = np.random.randn(num_points, dim)
    norms = np.linalg.norm(noise, axis=1, keepdims=True)
    return noise / norms


def mock_faces_data(embeddings):
    """Format embeddings into the expected database return format."""
    return [
        {"face_id": i, "embeddings": emb, "cluster_name": None}
        for i, emb in enumerate(embeddings)
    ]


class TestFaceClusteringAlgo:
    @patch("app.utils.face_clusters.db_get_all_faces_with_cluster_names")
    def test_folder_size_regression(self, mock_db_get):
        """Test 1: Folder-size regression (the original bug)"""
        # Generate 20 embeddings (2 identities, 10 points each)
        identity_embs, identity_labels = generate_synthetic_embeddings(
            num_identities=2, points_per_identity=10
        )

        # --- Run 1: Isolated run ---
        mock_db_get.return_value = mock_faces_data(identity_embs)

        # Run clustering with eps estimation disabled (by using fixed eps, though estimate_eps runs internally)
        # and strict similarity threshold.
        results_isolated, _ = cluster_util_cluster_all_face_embeddings(
            eps=0.75, min_samples=2, similarity_threshold=0.85
        )

        # Count clusters in isolated run
        isolated_clusters = set(r.cluster_uuid for r in results_isolated)
        assert (
            len(isolated_clusters) == 2
        ), f"The folder-size bug is present: expected 2 clusters, got {len(isolated_clusters)} in isolated run"

        # Verify points were assigned correctly (10 points per cluster)
        cluster_counts = {}
        for r in results_isolated:
            cluster_counts[r.cluster_uuid] = cluster_counts.get(r.cluster_uuid, 0) + 1

        for count in cluster_counts.values():
            assert (
                count >= 8
            ), f"Identity cluster should contain majority of points, got {count}"

        # --- Run 2: With noise ---
        noise_embs = generate_noise_embeddings(num_points=80)
        all_embs = np.vstack([identity_embs, noise_embs])

        mock_db_get.return_value = mock_faces_data(all_embs)

        results_noise, _ = cluster_util_cluster_all_face_embeddings(
            eps=0.75, min_samples=2, similarity_threshold=0.85
        )

        # We need to find the clusters containing the original identity points (face_ids 0 to 19)
        identity_results = [r for r in results_noise if r.face_id < 20]

        noise_run_identity_clusters = set(r.cluster_uuid for r in identity_results)
        assert (
            len(noise_run_identity_clusters) == 2
        ), f"Expected 2 clusters for identity points with noise, got {len(noise_run_identity_clusters)}"

    def test_adaptive_eps_stability(self):
        """Test 2: Adaptive eps stability"""
        identity_embs, _ = generate_synthetic_embeddings(
            num_identities=2, points_per_identity=10
        )

        sizes = [20, 50, 100]

        for size in sizes:
            num_noise = size - len(identity_embs)
            if num_noise > 0:
                noise_embs = generate_noise_embeddings(num_points=num_noise)
                test_embs = np.vstack([identity_embs, noise_embs])
            else:
                test_embs = identity_embs

            eps = estimate_eps(test_embs, k=2)

            assert eps is not None
            assert (
                0.0 < eps < 1.0
            ), f"eps value {eps} out of expected bounds for size {size}"

    def test_estimate_eps_fallback(self):
        """Test 3: estimate_eps() fallback"""
        # Empty array
        assert estimate_eps(np.array([]), k=2) is None

        # 1 element
        assert estimate_eps(np.random.randn(1, 512), k=2) is None

        # 2 elements
        assert estimate_eps(np.random.randn(2, 512), k=2) is None

    @patch("app.utils.face_clusters.db_get_all_faces_with_cluster_names")
    def test_adaptive_eps_clamping_regression(self, mock_db_get):
        """Test 4: Adaptive eps clamping under sparse datasets with singletons"""
        # Create 9 embeddings:
        # Identity A: 2 points (very close)
        # Identity B: 2 points (very close)
        # 5 Singleton points (completely random / orthogonal)
        dim = 512
        np.random.seed(42)

        # Identity A
        center_a = np.random.randn(dim)
        center_a /= np.linalg.norm(center_a)
        pt_a1 = center_a + np.random.randn(dim) * 0.01
        pt_a1 /= np.linalg.norm(pt_a1)
        pt_a2 = center_a + np.random.randn(dim) * 0.01
        pt_a2 /= np.linalg.norm(pt_a2)

        # Identity B (orthogonal to A)
        pt_b1 = np.random.randn(dim)
        pt_b1 -= np.dot(pt_b1, center_a) * center_a
        pt_b1 /= np.linalg.norm(pt_b1)
        pt_b2 = pt_b1 + np.random.randn(dim) * 0.01
        pt_b2 /= np.linalg.norm(pt_b2)

        # 5 Singletons (mutually orthogonal to each other and A/B)
        singletons = []
        for _ in range(5):
            vec = np.random.randn(dim)
            vec -= np.dot(vec, center_a) * center_a
            vec -= np.dot(vec, pt_b1) * pt_b1
            for prev in singletons:
                vec -= np.dot(vec, prev) * prev
            vec /= np.linalg.norm(vec)
            singletons.append(vec)

        all_embeddings = [pt_a1, pt_a2, pt_b1, pt_b2] + singletons

        # Mock database call
        mock_db_get.return_value = [
            {"face_id": i, "embeddings": emb, "cluster_name": None}
            for i, emb in enumerate(all_embeddings)
        ]

        # Run clustering with similarity_threshold=0.85 -> max_distance = 0.15
        results, _ = cluster_util_cluster_all_face_embeddings(
            min_samples=2, similarity_threshold=0.85
        )

        # Group face_ids by their cluster UUIDs
        clusters = {}
        for r in results:
            if r.cluster_uuid not in clusters:
                clusters[r.cluster_uuid] = []
            clusters[r.cluster_uuid].append(r.face_id)

        cluster_a_uuid = None
        cluster_b_uuid = None

        for cluster_uuid, face_ids in clusters.items():
            if 0 in face_ids:
                cluster_a_uuid = cluster_uuid
                assert 1 in face_ids, "Identity A faces should be grouped together"
                assert all(
                    f in [0, 1] for f in face_ids
                ), f"Identity A cluster contains unexpected faces: {face_ids}"
            elif 2 in face_ids:
                cluster_b_uuid = cluster_uuid
                assert 3 in face_ids, "Identity B faces should be grouped together"
                assert all(
                    f in [2, 3] for f in face_ids
                ), f"Identity B cluster contains unexpected faces: {face_ids}"

        assert cluster_a_uuid is not None, "Identity A was not clustered"
        assert cluster_b_uuid is not None, "Identity B was not clustered"
        assert (
            cluster_a_uuid != cluster_b_uuid
        ), "Identity A and Identity B should not be merged into the same cluster"

    def test_quality_gate(self):
        """Test 5: Quality gate unit tests"""
        # A sharp, large face crop should pass
        # Random noise image has high variance (sharp)
        np.random.seed(42)
        sharp_crop = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        assert (
            face_passes_quality_gate(
                face_crop=sharp_crop,
                bbox=(0, 0, 100, 100),
                conf_score=0.9,
                conf_threshold=0.45,
                blur_threshold=10.0,  # Random noise will be well above this
                min_face_size=400,
            )
            is True
        )

        # A blurred crop should fail
        # Flat image has zero variance
        blurred_crop = np.ones((100, 100, 3), dtype=np.uint8) * 128

        assert (
            face_passes_quality_gate(
                face_crop=blurred_crop,
                bbox=(0, 0, 100, 100),
                conf_score=0.9,
                conf_threshold=0.45,
                blur_threshold=10.0,
                min_face_size=400,
            )
            is False
        )

        # A small bbox should fail
        assert (
            face_passes_quality_gate(
                face_crop=sharp_crop,
                bbox=(0, 0, 10, 10),  # area = 100
                conf_score=0.9,
                conf_threshold=0.45,
                blur_threshold=10.0,
                min_face_size=400,
            )
            is False
        )

        # A low confidence score should fail
        assert (
            face_passes_quality_gate(
                face_crop=sharp_crop,
                bbox=(0, 0, 100, 100),
                conf_score=0.4,  # < 0.45
                conf_threshold=0.45,
                blur_threshold=10.0,
                min_face_size=400,
            )
            is False
        )

        # An empty crop should fail
        empty_crop = np.zeros((0, 0, 3), dtype=np.uint8)
        assert (
            face_passes_quality_gate(
                face_crop=empty_crop,
                bbox=(0, 0, 500, 500),
                conf_score=0.9,
                conf_threshold=0.45,
                blur_threshold=10.0,
                min_face_size=400,
            )
            is False
        )


# ##############################
# Stale cluster cleanup (issue #1023)
# ##############################


@pytest.fixture
def isolated_cluster_db(tmp_path, monkeypatch):
    """Point face_clusters/faces DB helpers at a disposable SQLite file.

    Each database module binds DATABASE_PATH at import time, so every module
    that opens a connection needs its own attribute patched directly.
    """
    db_path = str(tmp_path / "test_face_clusters.sqlite3")
    monkeypatch.setattr(face_clusters_db, "DATABASE_PATH", db_path)
    monkeypatch.setattr(faces_db, "DATABASE_PATH", db_path)
    monkeypatch.setattr(images_db, "DATABASE_PATH", db_path)
    monkeypatch.setattr(folders_db, "DATABASE_PATH", db_path)
    monkeypatch.setattr(yolo_db, "DATABASE_PATH", db_path)

    yolo_db.db_create_YOLO_classes_table()
    face_clusters_db.db_create_clusters_table()
    faces_db.db_create_faces_table()
    folders_db.db_create_folders_table()
    images_db.db_create_images_table()
    yield db_path


class TestEmptyClusterCleanup:
    """Removing a folder cascades away its faces, but the clusters those faces
    built are left behind. They must not keep surfacing in the UI."""

    def test_listing_excludes_clusters_with_no_faces(self, isolated_cluster_db):
        """A cluster whose faces are all gone is not returned to the caller."""
        face_clusters_db.db_insert_clusters_batch(
            [
                {
                    "cluster_id": "populated",
                    "cluster_name": "Has Faces",
                    "face_image_base64": "b64",
                },
                {
                    "cluster_id": "orphaned",
                    "cluster_name": "Folder Deleted",
                    "face_image_base64": "b64",
                },
            ]
        )
        faces_db.db_insert_face_embeddings(
            image_id="img-1",
            embeddings=np.ones(128),
            confidence=0.9,
            bbox={"x": 0, "y": 0, "width": 10, "height": 10},
            cluster_id="populated",
        )

        listed = face_clusters_db.db_get_all_clusters_with_face_counts()

        assert [c["cluster_id"] for c in listed] == ["populated"]

    def test_clusters_count_reflects_stored_rows(self, isolated_cluster_db):
        assert face_clusters_db.db_get_clusters_count() == 0

        face_clusters_db.db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": None, "face_image_base64": None}]
        )

        assert face_clusters_db.db_get_clusters_count() == 1


class TestReclusterWithNoFaces:
    """A forced recluster of an emptied library must clear stale clusters
    instead of raising and leaving them in place."""

    @patch("app.utils.face_clusters.db_get_all_faces_with_cluster_names")
    def test_cluster_all_embeddings_returns_pair_when_no_faces(self, mock_faces):
        """The no-faces path must return the same (results, skipped) shape as
        every other path -- callers unpack it into two names."""
        mock_faces.return_value = []

        assert cluster_util_cluster_all_face_embeddings() == ([], 0)

    @patch("app.utils.face_clusters.db_update_metadata")
    @patch("app.utils.face_clusters.db_delete_all_clusters")
    @patch("app.utils.face_clusters.get_db_connection")
    @patch("app.utils.face_clusters.db_get_all_faces_with_cluster_names")
    @patch("app.utils.face_clusters.db_get_metadata")
    def test_forced_recluster_clears_clusters_when_no_faces_remain(
        self, mock_metadata, mock_faces, mock_conn, mock_delete, mock_update_metadata
    ):
        mock_metadata.return_value = {"user_preferences": {}}
        mock_faces.return_value = []

        created, skipped = cluster_util_face_clusters_sync(force_full_reclustering=True)

        assert (created, skipped) == (0, 0)
        mock_delete.assert_called_once()

    @patch("app.utils.face_clusters.db_delete_all_clusters")
    @patch("app.utils.face_clusters.get_db_connection")
    @patch("app.utils.face_clusters.db_update_face_cluster_ids_batch")
    @patch(
        "app.utils.face_clusters.cluster_util_assign_cluster_to_faces_without_clusterId"
    )
    @patch("app.utils.face_clusters.cluster_util_is_reclustering_needed")
    @patch("app.utils.face_clusters.db_get_metadata")
    def test_incremental_pass_never_deletes_clusters(
        self,
        mock_metadata,
        mock_needed,
        mock_assign,
        mock_update_batch,
        mock_conn,
        mock_delete,
    ):
        """Only a full recluster rebuilds from scratch; the incremental path
        must leave existing clusters alone."""
        mock_metadata.return_value = {"user_preferences": {}}
        mock_needed.return_value = False
        mock_assign.return_value = ([{"face_id": 1, "cluster_id": "c1"}], 0)

        cluster_util_face_clusters_sync()

        mock_delete.assert_not_called()


class TestReclusteringNeededBootstrap:
    """Incremental assignment matches faces against existing cluster means, so
    it can never create the first cluster -- that case needs a full pass."""

    @patch("app.utils.face_clusters.db_get_clusters_count")
    @patch("app.utils.face_clusters.db_get_faces_unassigned_clusters")
    def test_full_pass_forced_when_no_clusters_exist_yet(
        self, mock_unassigned, mock_count
    ):
        mock_unassigned.return_value = [{"face_id": i} for i in range(50)]
        mock_count.return_value = 0

        assert cluster_util_is_reclustering_needed({"user_preferences": {}}) is True

    @patch("app.utils.face_clusters.db_get_clusters_count")
    @patch("app.utils.face_clusters.db_get_faces_unassigned_clusters")
    def test_incremental_still_used_once_clusters_exist(
        self, mock_unassigned, mock_count
    ):
        """Guard against over-correcting into a full recluster every sync."""
        mock_unassigned.return_value = [{"face_id": i} for i in range(50)]
        mock_count.return_value = 3

        assert cluster_util_is_reclustering_needed({"user_preferences": {}}) is False

    @patch("app.utils.face_clusters.db_get_clusters_count")
    @patch("app.utils.face_clusters.db_get_faces_unassigned_clusters")
    def test_no_faces_and_no_clusters_does_not_force_a_pass(
        self, mock_unassigned, mock_count
    ):
        """An empty library has nothing to bootstrap from."""
        mock_unassigned.return_value = []
        mock_count.return_value = 0

        assert cluster_util_is_reclustering_needed({"user_preferences": {}}) is False
