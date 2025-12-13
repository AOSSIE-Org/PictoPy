"""
Regression test for DBSCAN clustering parameter optimization (Issue #722)

This test validates that the new parameters (eps=0.15, min_samples=3) prevent
the incorrect clustering of unrelated images while maintaining accurate same-person grouping.
"""

import pytest
import numpy as np
import uuid
from sklearn.cluster import DBSCAN
from app.utils.face_clusters import cluster_util_cluster_all_face_embeddings


class TestClusteringRegression:
    """Regression tests for face clustering bug #722"""

    def test_dbscan_default_parameters(self):
        """Test that default parameters are correctly set to prevent issue #722"""
        import inspect
        
        sig = inspect.signature(cluster_util_cluster_all_face_embeddings)
        eps_default = sig.parameters['eps'].default
        min_samples_default = sig.parameters['min_samples'].default
        
        assert eps_default == 0.15, f"eps should be 0.15, got {eps_default}"
        assert min_samples_default == 3, f"min_samples should be 3, got {min_samples_default}"

    def test_prevents_large_incorrect_clusters(self):
        """
        Test that new parameters prevent large incorrect clusters.
        
        Simulates the issue #722 scenario where unrelated faces were clustered together.
        """
        np.random.seed(42)
        
        # Simulate 3 distinct people with different face embeddings
        # Person 1: embeddings around [0.1, 0.1, ...]
        person1_base = np.array([0.1] * 128)
        person1_faces = [person1_base + np.random.normal(0, 0.03, 128) for _ in range(5)]
        
        # Person 2: embeddings around [0.5, 0.5, ...] (very different from person 1)
        person2_base = np.array([0.5] * 128)
        person2_faces = [person2_base + np.random.normal(0, 0.03, 128) for _ in range(5)]
        
        # Person 3: embeddings around [0.9, 0.9, ...] (very different from both)
        person3_base = np.array([0.9] * 128)
        person3_faces = [person3_base + np.random.normal(0, 0.03, 128) for _ in range(5)]
        
        all_embeddings = np.array(person1_faces + person2_faces + person3_faces)
        
        # Test with NEW parameters (should create separate clusters)
        dbscan_new = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels_new = dbscan_new.fit_predict(all_embeddings)
        n_clusters_new = len(set(labels_new)) - (1 if -1 in labels_new else 0)
        
        # Should create exactly 3 separate clusters (one per person)
        assert n_clusters_new == 3, f"Expected exactly 3 clusters (one per person), got {n_clusters_new}"
        
        # No single cluster should contain all 15 faces (the bug scenario)
        cluster_sizes = {}
        for label in labels_new:
            if label != -1:
                cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
        
        max_cluster_size = max(cluster_sizes.values()) if cluster_sizes else 0
        assert max_cluster_size < 15, f"Found cluster with {max_cluster_size} faces (should be < 15)"

    def test_maintains_same_person_clustering(self):
        """
        Test that new parameters still cluster same-person faces together.
        
        Ensures the fix doesn't over-fragment legitimate clusters.
        """
        np.random.seed(42)
        
        # Simulate same person with 5 very similar face embeddings
        # (small variance, cosine distance < 0.15)
        person_base = np.array([0.5] * 128)
        same_person_faces = [person_base + np.random.normal(0, 0.02, 128) for _ in range(5)]
        
        embeddings = np.array(same_person_faces)
        
        # Test with NEW parameters
        dbscan_new = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels_new = dbscan_new.fit_predict(embeddings)
        n_clusters_new = len(set(labels_new)) - (1 if -1 in labels_new else 0)
        
        # Should create 1 cluster for the same person
        assert n_clusters_new == 1, f"Same person faces should form 1 cluster, got {n_clusters_new}"
        
        # All faces should be in the same cluster (not noise)
        assert -1 not in labels_new, "Same person faces should not be marked as noise"

    def test_min_samples_threshold_enforcement(self):
        """Test that min_samples=3 is properly enforced"""
        np.random.seed(42)
        
        # Create 2 similar faces (below min_samples threshold)
        person_base = np.array([0.5] * 128)
        two_faces = [person_base + np.random.normal(0, 0.02, 128) for _ in range(2)]
        
        embeddings = np.array(two_faces)
        
        # Test with NEW parameters (min_samples=3)
        dbscan_new = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels_new = dbscan_new.fit_predict(embeddings)
        
        # Should NOT form a cluster (below min_samples threshold)
        # Both should be marked as noise (-1)
        assert all(label == -1 for label in labels_new), \
            "Faces below min_samples threshold should be marked as noise"

    def test_old_vs_new_parameters_comparison(self):
        """
        Compare clustering behavior between old and new parameters.
        
        Demonstrates that new parameters are more restrictive.
        """
        np.random.seed(42)
        
        # Create diverse embeddings (mix of similar and dissimilar)
        embeddings_list = []
        for i in range(3):
            base = np.array([i * 0.3] * 128)
            faces = [base + np.random.normal(0, 0.05, 128) for _ in range(4)]
            embeddings_list.extend(faces)
        
        embeddings = np.array(embeddings_list)
        
        # Test with OLD parameters
        dbscan_old = DBSCAN(eps=0.3, min_samples=2, metric="cosine")
        labels_old = dbscan_old.fit_predict(embeddings)
        n_clusters_old = len(set(labels_old)) - (1 if -1 in labels_old else 0)
        
        # Test with NEW parameters
        dbscan_new = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels_new = dbscan_new.fit_predict(embeddings)
        n_clusters_new = len(set(labels_new)) - (1 if -1 in labels_new else 0)
        n_noise_new = list(labels_new).count(-1)
        n_noise_old = list(labels_old).count(-1)
        
        # New parameters should be more restrictive:
        # Should have more noise points or more separate clusters (less incorrect merging)
        # With tighter eps=0.15, dissimilar faces should form separate clusters
        is_more_restrictive = (
            n_noise_new > n_noise_old or  # More noise
            n_clusters_new >= n_clusters_old  # Same or more clusters (less merging)
        )
        assert is_more_restrictive, \
            f"New parameters should be more restrictive (old: {n_clusters_old} clusters, {n_noise_old} noise; new: {n_clusters_new} clusters, {n_noise_new} noise)"


class TestClusteringEdgeCases:
    """Edge case tests for clustering"""

    def test_empty_embeddings(self):
        """Test behavior with no embeddings"""
        embeddings = np.array([]).reshape(0, 128)
        
        dbscan = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        
        # Should return empty labels for empty input
        labels = dbscan.fit_predict(embeddings)
        assert len(labels) == 0, f"Expected empty labels for empty input, got {len(labels)}"

    def test_single_embedding(self):
        """Test behavior with single embedding"""
        embedding = np.array([[0.5] * 128])
        
        dbscan = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels = dbscan.fit_predict(embedding)
        
        # Single face should be noise (below min_samples)
        assert labels[0] == -1

    def test_exact_min_samples_threshold(self):
        """Test behavior with exactly min_samples faces"""
        np.random.seed(42)
        
        # Create exactly 3 very similar faces
        person_base = np.array([0.5] * 128)
        three_faces = [person_base + np.random.normal(0, 0.02, 128) for _ in range(3)]
        
        embeddings = np.array(three_faces)
        
        dbscan = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        labels = dbscan.fit_predict(embeddings)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Should form exactly 1 cluster
        assert n_clusters == 1, f"Expected 1 cluster with 3 faces, got {n_clusters}"


class TestClusteringIntegration:
    """Integration tests for full clustering pipeline"""

    def test_clustering_pipeline_with_new_parameters(self, mocker):
        """
        Test full clustering pipeline with new default parameters.
        
        This validates the complete flow including database operations,
        UUID generation, and cluster naming logic.
        """
        np.random.seed(42)
        
        # Create test data: 3 people with 4 faces each
        test_data = []
        for person_id in range(3):
            base = np.array([person_id * 0.3] * 128)
            for face_num in range(4):
                embedding = base + np.random.normal(0, 0.03, 128)
                test_data.append({
                    "face_id": person_id * 4 + face_num,
                    "embeddings": embedding.tolist(),
                    "cluster_name": None
                })
        
        # Mock the database call
        mocker.patch(
            'app.utils.face_clusters.db_get_all_faces_with_cluster_names',
            return_value=test_data
        )
        
        # Call the actual clustering function
        results = cluster_util_cluster_all_face_embeddings()
        
        # Validate results structure
        assert len(results) > 0, "Should return clustering results"
        assert len(results) == 12, f"Expected 12 results (3 people × 4 faces), got {len(results)}"
        
        # Validate ClusterResult objects
        for result in results:
            assert hasattr(result, 'face_id'), "Result should have face_id"
            assert hasattr(result, 'embedding'), "Result should have embedding"
            assert hasattr(result, 'cluster_uuid'), "Result should have cluster_uuid"
            assert hasattr(result, 'cluster_name'), "Result should have cluster_name"
        
        # Validate clustering behavior with new parameters
        cluster_ids = set(r.cluster_uuid for r in results)
        assert len(cluster_ids) == 3, f"Expected 3 distinct clusters, got {len(cluster_ids)}"
        
        # Validate each cluster has exactly 4 faces
        cluster_counts = {}
        for result in results:
            cluster_counts[result.cluster_uuid] = cluster_counts.get(result.cluster_uuid, 0) + 1
        
        for cluster_id, count in cluster_counts.items():
            assert count == 4, f"Each cluster should have 4 faces, cluster {cluster_id} has {count}"
        
        # Validate UUIDs are valid
        for result in results:
            try:
                uuid.UUID(result.cluster_uuid)
            except ValueError:
                pytest.fail(f"Invalid UUID: {result.cluster_uuid}")

    def test_clustering_prevents_large_incorrect_clusters_integration(self, mocker):
        """
        Integration test specifically for issue #722 scenario.
        
        Validates that the full pipeline prevents the 314-image incorrect cluster.
        """
        np.random.seed(42)
        
        # Simulate many diverse faces (like the 314-image scenario)
        test_data = []
        for i in range(50):  # 50 different people
            base = np.array([i * 0.05] * 128)
            # Each person has 2-3 faces
            num_faces = 2 if i % 2 == 0 else 3
            for j in range(num_faces):
                embedding = base + np.random.normal(0, 0.03, 128)
                test_data.append({
                    "face_id": len(test_data),
                    "embeddings": embedding.tolist(),
                    "cluster_name": None
                })
        
        # Mock the database call
        mocker.patch(
            'app.utils.face_clusters.db_get_all_faces_with_cluster_names',
            return_value=test_data
        )
        
        # Call the actual clustering function
        results = cluster_util_cluster_all_face_embeddings()
        
        # Validate no single cluster contains all faces (the bug scenario)
        cluster_counts = {}
        for result in results:
            cluster_counts[result.cluster_uuid] = cluster_counts.get(result.cluster_uuid, 0) + 1
        
        max_cluster_size = max(cluster_counts.values()) if cluster_counts else 0
        total_faces = len(test_data)
        
        # No cluster should contain more than 20% of total faces
        max_allowed = total_faces * 0.2
        assert max_cluster_size < max_allowed, \
            f"Found cluster with {max_cluster_size} faces (max allowed: {max_allowed}). This indicates the bug is not fixed."

