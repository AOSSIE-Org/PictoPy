"""
Conservative Face Clustering Module

This module implements a conservative face clustering approach that prioritizes
NOT merging different people over grouping all photos of the same person.

Key principles:
1. Use strict distance thresholds - prefer more clusters over incorrect merges
2. Validate clusters by checking intra-cluster distance variance
3. Never merge clusters post-hoc unless extremely confident
4. Handle varying dataset sizes gracefully

This replaces the previous MDPC implementation with a simpler, more reliable approach.
"""

import numpy as np
from typing import List
from numpy.typing import NDArray
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_distances
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from collections import defaultdict


def compute_pairwise_distances(embeddings: NDArray) -> NDArray:
    """Compute pairwise cosine distances."""
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)
    return cosine_distances(normalized)


def select_conservative_epsilon(embeddings: NDArray, k: int = 5) -> float:
    """
    Select a conservative epsilon that prevents over-merging.

    Uses the k-NN distance distribution and selects an epsilon that
    groups only clearly similar faces.
    """
    n_samples = len(embeddings)
    k = min(k, n_samples - 1)

    if k < 1:
        return 0.3  # Default conservative value

    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    nbrs = NearestNeighbors(n_neighbors=k + 1, metric="cosine")
    nbrs.fit(normalized)
    distances, _ = nbrs.kneighbors(normalized)

    # Use k-th neighbor distances
    k_distances = distances[:, -1]

    # Adaptive percentile based on distance statistics
    # If data is naturally tight, we can be stricter
    # If data is spread out, we need to be more lenient
    median_dist = np.median(k_distances)

    if median_dist < 0.3:
        # Tight data - use lower percentile
        eps = np.percentile(k_distances, 35)
    elif median_dist < 0.5:
        # Moderate spread - use median
        eps = np.percentile(k_distances, 45)
    else:
        # Wide spread (different people) - be conservative
        eps = np.percentile(k_distances, 25)

    # Clamp to reasonable range for face embeddings
    # Cosine distance for same person is typically 0.1-0.4
    # Different people are typically > 0.5
    eps = np.clip(eps, 0.18, 0.40)

    return float(eps)


def validate_cluster(embeddings: NDArray, max_diameter: float = 0.5) -> bool:
    """
    Validate that a cluster is tight enough to be a single person.

    Returns False if the cluster is too spread out (likely multiple people).
    """
    if len(embeddings) < 2:
        return True

    # Compute pairwise distances
    distances = compute_pairwise_distances(embeddings)

    # Check maximum distance (diameter)
    max_dist = np.max(distances)

    return max_dist <= max_diameter


def split_loose_cluster(
    embeddings: NDArray, face_indices: NDArray, max_diameter: float = 0.4
) -> List[NDArray]:
    """
    Split a cluster that's too loose into tighter sub-clusters.

    Returns list of index arrays for sub-clusters.
    """
    if len(embeddings) < 4:
        return [face_indices]

    # Try hierarchical clustering with strict threshold
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=max_diameter,
        metric="cosine",
        linkage="complete",  # Complete linkage = all pairs must be within threshold
    )

    try:
        sub_labels = clustering.fit_predict(embeddings)

        # Group indices by sub-cluster
        sub_clusters = defaultdict(list)
        for i, label in enumerate(sub_labels):
            sub_clusters[label].append(face_indices[i])

        return [np.array(indices) for indices in sub_clusters.values()]
    except Exception:
        return [face_indices]


class ConservativeFaceClustering:
    """
    Conservative face clustering that prioritizes accuracy over completeness.

    This means it will sometimes split the same person into multiple clusters,
    but will very rarely merge different people into the same cluster.

    The algorithm now includes a safe merge step to re-merge clusters that
    were over-split (same person, different angles).
    """

    def __init__(
        self,
        eps: float = 0.25,
        min_samples: int = 2,
        max_cluster_diameter: float = 0.60,
        validate_clusters: bool = True,
        auto_eps: bool = True,
        merge_close_clusters: bool = True,
        merge_threshold: float = 0.40,
    ):
        """
        Initialize conservative clustering.

        Args:
            eps: Maximum distance for DBSCAN (default: 0.25 - conservative)
            min_samples: Minimum samples for core point (default: 2)
            max_cluster_diameter: Maximum allowed cluster diameter (default: 0.60)
            validate_clusters: Whether to validate and split loose clusters
            auto_eps: Auto-select conservative epsilon
            merge_close_clusters: Whether to merge clusters that are clearly same person
            merge_threshold: Max centroid distance for merging (default: 0.40)
        """
        self.eps = eps
        self.min_samples = max(min_samples, 2)  # Never allow 1
        self.max_cluster_diameter = max_cluster_diameter
        self.validate_clusters = validate_clusters
        self.auto_eps = auto_eps
        self.merge_close_clusters = merge_close_clusters
        self.merge_threshold = merge_threshold

    def fit_predict(self, embeddings: NDArray) -> NDArray:
        """
        Perform conservative clustering on face embeddings.
        """
        n_samples = len(embeddings)

        if n_samples < 2:
            return np.zeros(n_samples, dtype=int)

        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / np.maximum(norms, 1e-10)

        # Select epsilon
        if self.auto_eps:
            eps = select_conservative_epsilon(normalized)
        else:
            eps = self.eps

        # Initial DBSCAN clustering with conservative parameters
        dbscan = DBSCAN(
            eps=eps,
            min_samples=self.min_samples,
            metric="cosine",
        )
        labels = dbscan.fit_predict(normalized)

        # Validate and potentially split clusters
        if self.validate_clusters:
            labels = self._validate_and_split_clusters(normalized, labels)

        # Safe merge step: merge clusters that are clearly same person
        if self.merge_close_clusters:
            labels = self._safe_merge_clusters(normalized, labels)

        # Relabel to consecutive integers
        return self._relabel_consecutive(labels)

    def _validate_and_split_clusters(
        self, embeddings: NDArray, labels: NDArray
    ) -> NDArray:
        """
        Validate each cluster and split if too loose.
        """
        new_labels = labels.copy()
        unique_labels = set(labels) - {-1}
        next_label = max(labels) + 1 if len(labels) > 0 else 0

        for label in unique_labels:
            mask = labels == label
            cluster_indices = np.where(mask)[0]
            cluster_embeddings = embeddings[mask]

            # Check if cluster is valid
            if not validate_cluster(cluster_embeddings, self.max_cluster_diameter):
                # Split the cluster
                sub_clusters = split_loose_cluster(
                    cluster_embeddings,
                    cluster_indices,
                    max_diameter=self.max_cluster_diameter * 0.8,
                )

                if len(sub_clusters) > 1:
                    # Apply new labels
                    for i, sub_indices in enumerate(sub_clusters):
                        if i == 0:
                            # Keep original label for first sub-cluster
                            continue
                        if len(sub_indices) >= self.min_samples:
                            new_labels[sub_indices] = next_label
                            next_label += 1
                        else:
                            # Too small, mark as noise
                            new_labels[sub_indices] = -1

        return new_labels

    def _safe_merge_clusters(self, embeddings: NDArray, labels: NDArray) -> NDArray:
        """
        Safely merge clusters that are clearly the same person.

        This handles the case where the same person with different face angles
        gets split into multiple clusters. We use TWO merge strategies:

        1. Centroid distance: merge if centroids are very close
        2. Minimum pairwise distance: merge if ANY face in cluster A is very
           close to ANY face in cluster B (handles angle variation)

        We only merge if the merged cluster would still be valid (diameter check).
        """
        new_labels = labels.copy()
        unique_labels = sorted(set(labels) - {-1})

        if len(unique_labels) < 2:
            return new_labels

        # Calculate centroids and collect embeddings for each cluster
        cluster_data = {}
        for label in unique_labels:
            mask = labels == label
            cluster_emb = embeddings[mask]
            centroid = np.mean(cluster_emb, axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            cluster_data[label] = {
                "centroid": centroid,
                "embeddings": cluster_emb,
                "indices": np.where(mask)[0],
            }

        # Use Union-Find for transitive merges
        parent = {label: label for label in unique_labels}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Check all pairs of clusters
        for i, label_i in enumerate(unique_labels):
            for label_j in unique_labels[i + 1 :]:
                # Skip if already in same group
                if find(label_i) == find(label_j):
                    continue

                data_i = cluster_data[label_i]
                data_j = cluster_data[label_j]

                # Strategy 1: Centroid distance
                centroid_dist = 1 - np.dot(data_i["centroid"], data_j["centroid"])

                # Strategy 2: Minimum pairwise distance between clusters
                # This handles angle variation better
                cross_distances = cosine_distances(
                    data_i["embeddings"], data_j["embeddings"]
                )
                min_dist = np.min(cross_distances)

                # Also check: what fraction of faces have a close match in other cluster?
                # This prevents merging when only 1-2 outlier faces are close
                close_threshold = self.merge_threshold
                close_matches_i = np.any(
                    cross_distances < close_threshold, axis=1
                ).sum()
                close_matches_j = np.any(
                    cross_distances < close_threshold, axis=0
                ).sum()

                # At least 30% of smaller cluster should have close matches
                min_size = min(len(data_i["embeddings"]), len(data_j["embeddings"]))
                match_ratio = max(close_matches_i, close_matches_j) / min_size

                should_merge = False

                # Merge if centroids are very close
                if centroid_dist < self.merge_threshold * 0.8:
                    should_merge = True
                # Or merge if minimum distance is very small AND good match ratio
                elif min_dist < self.merge_threshold * 0.6 and match_ratio >= 0.3:
                    should_merge = True
                # Or merge if there are many cross-matches
                elif match_ratio >= 0.5 and min_dist < self.merge_threshold:
                    should_merge = True

                if should_merge:
                    # Validate merged cluster would be okay
                    root_i = find(label_i)
                    root_j = find(label_j)

                    # Get all embeddings that would be merged
                    combined_indices = []
                    for label in unique_labels:
                        if find(label) in (root_i, root_j):
                            combined_indices.extend(
                                cluster_data[label]["indices"].tolist()
                            )

                    combined_emb = embeddings[combined_indices]

                    # Only merge if combined cluster is still valid
                    if validate_cluster(combined_emb, self.max_cluster_diameter):
                        union(label_i, label_j)

        # Apply merges
        for label in unique_labels:
            root = find(label)
            if root != label:
                new_labels[labels == label] = root

        return new_labels

    def _relabel_consecutive(self, labels: NDArray) -> NDArray:
        """Relabel clusters to consecutive integers starting from 0."""
        unique_labels = sorted(set(labels) - {-1})
        label_map = {old: new for new, old in enumerate(unique_labels)}
        label_map[-1] = -1
        return np.array([label_map[label] for label in labels])


def cluster_conservative(
    embeddings: NDArray,
    eps: float = 0.25,
    min_samples: int = 2,
    max_cluster_diameter: float = 0.60,
    validate: bool = True,
    auto_eps: bool = True,
    merge_close_clusters: bool = True,
    merge_threshold: float = 0.40,
) -> NDArray:
    """
    Convenience function for conservative clustering.

    Args:
        embeddings: Face embeddings array
        eps: DBSCAN epsilon (max distance for neighbors)
        min_samples: Minimum samples for DBSCAN core point
        max_cluster_diameter: Maximum diameter for valid clusters
        validate: Whether to validate and split loose clusters
        auto_eps: Auto-select epsilon based on data
        merge_close_clusters: Whether to merge clearly same-person clusters
        merge_threshold: Max centroid distance for merging
    """
    clusterer = ConservativeFaceClustering(
        eps=eps,
        min_samples=min_samples,
        max_cluster_diameter=max_cluster_diameter,
        validate_clusters=validate,
        auto_eps=auto_eps,
        merge_close_clusters=merge_close_clusters,
        merge_threshold=merge_threshold,
    )
    return clusterer.fit_predict(embeddings)
