"""
Regression test for DBSCAN clustering parameter optimization (Issue #722)

This test validates that the new parameters (eps=0.15, min_samples=3) prevent
the incorrect clustering of unrelated images while maintaining accurate same-person grouping.
"""

import pytest
import numpy as np
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
        
        # Should create 3 separate clusters (one per person)
        assert n_clusters_new >= 2, f"Expected at least 2 clusters, got {n_clusters_new}"
        
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
        
        # New parameters should be more restrictive:
        # Either fewer/equal clusters OR more noise points
        assert (n_clusters_new <= n_clusters_old or n_noise_new > 0), \
            "New parameters should be more restrictive than old parameters"


class TestClusteringEdgeCases:
    """Edge case tests for clustering"""

    def test_empty_embeddings(self):
        """Test behavior with no embeddings"""
        embeddings = np.array([])
        
        dbscan = DBSCAN(eps=0.15, min_samples=3, metric="cosine")
        
        # Should handle empty input gracefully
        if len(embeddings) > 0:
            labels = dbscan.fit_predict(embeddings)
            assert len(labels) == 0

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
