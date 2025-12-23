"""
Advanced Face Clustering Module

This module provides the main entry point for face clustering.
Uses conservative clustering by default which prioritizes accuracy.

IMPORTANT: min_samples >= 2 is enforced to prevent bridge point chaining.
"""

import numpy as np
from typing import Optional, Dict, Any
from numpy.typing import NDArray
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
from sklearn.neighbors import NearestNeighbors

from app.utils.clustering_conservative import (
    cluster_conservative,
    select_conservative_epsilon,
)


def calculate_adaptive_eps(
    embeddings: NDArray, k: int = 5, percentile: float = 50
) -> float:
    """
    Calculate adaptive epsilon using k-NN distance distribution.

    This method estimates the natural clustering scale from the data itself,
    providing a data-driven epsilon value for DBSCAN.

    Args:
        embeddings: Face embeddings array
        k: Number of nearest neighbors to consider
        percentile: Percentile of k-NN distances to use (default: median)

    Returns:
        Adaptive epsilon value
    """
    n_samples = len(embeddings)
    k = min(k, n_samples - 1)

    if k < 1:
        return 0.3  # Default

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # Fit NearestNeighbors
    nbrs = NearestNeighbors(n_neighbors=k + 1, metric="cosine")
    nbrs.fit(normalized)
    distances, _ = nbrs.kneighbors(normalized)

    # Use k-th neighbor distances (excluding self-distance at index 0)
    k_distances = distances[:, -1]

    # Calculate percentile
    eps = np.percentile(k_distances, percentile)

    # Clamp to reasonable range
    eps = np.clip(eps, 0.15, 0.5)

    return float(eps)


def cluster_faces_dbscan(
    embeddings: NDArray,
    eps: float = 0.3,
    min_samples: int = 2,  # Changed default from 1 to 2
    auto_eps: bool = True,
) -> NDArray:
    """
    Cluster face embeddings using DBSCAN with conservative settings.

    IMPORTANT: min_samples is now enforced to be >= 2 to prevent the
    "bridge point" problem where single faces connect separate clusters.

    Args:
        embeddings: Face embeddings (n_faces, embedding_dim)
        eps: Maximum distance for neighbors (ignored if auto_eps=True)
        min_samples: Minimum samples for core point (enforced >= 2)
        auto_eps: Automatically select epsilon from data

    Returns:
        Cluster labels (-1 for noise)
    """
    n_samples = len(embeddings)

    if n_samples < 2:
        return np.zeros(n_samples, dtype=int)

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # Calculate adaptive epsilon if requested
    if auto_eps:
        # Use conservative epsilon selection
        eps = select_conservative_epsilon(normalized, k=5)

    # CRITICAL: Enforce min_samples >= 2
    # This prevents bridge points from connecting separate clusters
    min_samples = max(min_samples, 2)

    # Run DBSCAN
    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="cosine",
    )
    labels = clustering.fit_predict(normalized)

    return labels


def cluster_faces_hierarchical(
    embeddings: NDArray,
    n_clusters: Optional[int] = None,
    distance_threshold: float = 0.5,
) -> NDArray:
    """
    Cluster face embeddings using hierarchical clustering.

    Uses complete linkage which ensures all pairs in a cluster
    are within the distance threshold (conservative).

    Args:
        embeddings: Face embeddings (n_faces, embedding_dim)
        n_clusters: Number of clusters (mutually exclusive with distance_threshold)
        distance_threshold: Max distance within cluster (if n_clusters is None)

    Returns:
        Cluster labels
    """
    n_samples = len(embeddings)

    if n_samples < 2:
        return np.zeros(n_samples, dtype=int)

    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # Setup clustering
    if n_clusters is not None:
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric="cosine",
            linkage="complete",  # Conservative: all pairs must be similar
        )
    else:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric="cosine",
            linkage="complete",
        )

    labels = clustering.fit_predict(normalized)
    return labels


def cluster_faces(
    embeddings: NDArray,
    algorithm: str = "conservative",
    eps: float = 0.25,
    min_samples: int = 2,
    max_cluster_diameter: float = 0.60,
    auto_eps: bool = True,
    distance_threshold: float = 0.5,
    n_clusters: Optional[int] = None,
    merge_close_clusters: bool = True,
    merge_threshold: float = 0.40,
    **kwargs,
) -> NDArray:
    """
    Main entry point for face clustering.

    Supports multiple algorithms with conservative as the recommended default.

    Args:
        embeddings: Face embeddings array
        algorithm: Clustering algorithm ("conservative", "dbscan", "hierarchical")
        eps: DBSCAN epsilon
        min_samples: Minimum samples per cluster
        max_cluster_diameter: Max diameter for conservative clustering
        auto_eps: Auto-select epsilon
        distance_threshold: For hierarchical clustering
        n_clusters: For hierarchical clustering (optional)
        merge_close_clusters: Whether to merge same-person clusters
        merge_threshold: Threshold for merging
        **kwargs: Additional algorithm-specific parameters

    Returns:
        Cluster labels (-1 for noise points)
    """
    algorithm = algorithm.lower()

    if algorithm in ("conservative", "default", "recommended"):
        return cluster_conservative(
            embeddings,
            eps=eps,
            min_samples=min_samples,
            max_cluster_diameter=max_cluster_diameter,
            auto_eps=auto_eps,
            merge_close_clusters=merge_close_clusters,
            merge_threshold=merge_threshold,
        )

    elif algorithm == "dbscan":
        return cluster_faces_dbscan(
            embeddings,
            eps=eps,
            min_samples=max(min_samples, 2),
            auto_eps=auto_eps,
        )

    elif algorithm in ("hierarchical", "agglomerative"):
        return cluster_faces_hierarchical(
            embeddings,
            n_clusters=n_clusters,
            distance_threshold=distance_threshold,
        )

    else:
        raise ValueError(
            f"Unknown algorithm: {algorithm}. Use 'conservative', 'dbscan', or 'hierarchical'."
        )


def get_cluster_stats(embeddings: NDArray, labels: NDArray) -> Dict[str, Any]:
    """
    Calculate statistics about the clustering result.

    Args:
        embeddings: Face embeddings
        labels: Cluster labels

    Returns:
        Dictionary with cluster statistics
    """
    unique_labels = set(labels) - {-1}
    n_clusters = len(unique_labels)
    n_noise = np.sum(labels == -1)

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # Calculate per-cluster stats
    cluster_sizes = []
    cluster_diameters = []
    cluster_densities = []

    for label in unique_labels:
        mask = labels == label
        cluster_emb = normalized[mask]
        cluster_sizes.append(np.sum(mask))

        if len(cluster_emb) > 1:
            distances = cosine_distances(cluster_emb)
            diameter = np.max(distances)
            avg_dist = np.mean(distances[np.triu_indices(len(cluster_emb), k=1)])
            cluster_diameters.append(diameter)
            cluster_densities.append(1.0 / (avg_dist + 1e-10))
        else:
            cluster_diameters.append(0.0)
            cluster_densities.append(float("inf"))

    return {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "n_total": len(labels),
        "cluster_sizes": cluster_sizes,
        "avg_cluster_size": np.mean(cluster_sizes) if cluster_sizes else 0,
        "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
        "min_cluster_size": min(cluster_sizes) if cluster_sizes else 0,
        "cluster_diameters": cluster_diameters,
        "avg_diameter": np.mean(cluster_diameters) if cluster_diameters else 0,
        "max_diameter": max(cluster_diameters) if cluster_diameters else 0,
    }


def calculate_cluster_mean(embeddings: NDArray) -> NDArray:
    """
    Calculate the mean embedding for a cluster.

    Args:
        embeddings: Face embeddings for a cluster

    Returns:
        Normalized mean embedding
    """
    if len(embeddings) == 0:
        return np.zeros(512)  # Default embedding dimension

    # Normalize all embeddings first
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # Calculate mean
    mean = np.mean(normalized, axis=0)

    # Normalize the mean
    mean_norm = np.linalg.norm(mean)
    if mean_norm > 1e-10:
        mean = mean / mean_norm

    return mean


# Backwards compatibility - keep old function names working
def advanced_face_clustering(
    embeddings: NDArray, algorithm: str = "conservative", **kwargs
) -> NDArray:
    """Alias for cluster_faces for backwards compatibility."""
    return cluster_faces(embeddings, algorithm=algorithm, **kwargs)


# Re-export for convenience
__all__ = [
    "cluster_faces",
    "cluster_faces_dbscan",
    "cluster_faces_hierarchical",
    "cluster_conservative",
    "calculate_adaptive_eps",
    "calculate_cluster_mean",
    "get_cluster_stats",
    "advanced_face_clustering",
]
