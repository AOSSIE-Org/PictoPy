import numpy as np
import uuid
from datetime import datetime
from sklearn.cluster import DBSCAN
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Union
from numpy.typing import NDArray

from app.database.faces import (
    db_get_all_faces_with_cluster_names,
    db_update_face_cluster_ids_batch,
    db_get_faces_unassigned_clusters,
    db_get_cluster_mean_embeddings,
)
from app.database.face_clusters import db_delete_all_clusters, db_insert_clusters_batch

from app.database.metadata import (
    db_get_metadata,
    db_update_metadata,
)


class ClusterResult:
    """Result class for clustering operation"""

    def __init__(self, face_id: int, embedding: NDArray, cluster_uuid: str, cluster_name: Optional[str]):
        self.face_id = face_id
        self.embedding = embedding
        self.cluster_uuid = cluster_uuid
        self.cluster_name = cluster_name

    def to_dict(self) -> Dict[str, Union[int, NDArray, str, None]]:
        """Convert to dictionary format"""
        return {
            "face_id": self.face_id,
            "embedding": self.embedding,
            "cluster_id": self.cluster_uuid,
            "cluster_name": self.cluster_name,
        }


def cluster_util_is_reclustering_needed(metadata) -> bool:
    """
    Check if reclustering is needed based on:
    1. Time since last clustering (24 hours)
    2. Number of faces without cluster ID (> 100)

    Returns:
        bool: True if reclustering is needed, False otherwise
    """
    if not metadata:
        return True  # No metadata means we need to recluster

    last_reclustering_time = metadata.get("reclustering_time")

    # Check if more than 24 hours have passed since last reclustering
    if last_reclustering_time:
        try:
            last_time = datetime.fromtimestamp(float(last_reclustering_time))
            time_since_last_reclustering = (datetime.now() - last_time).total_seconds()
            if time_since_last_reclustering > 86400:  # 24 hours in seconds
                return True
        except (ValueError, TypeError):
            # If we can't parse the time, assume we need to recluster
            return True

    # Check if number of faces without cluster ID is greater than 100
    unassigned_faces = db_get_faces_unassigned_clusters()
    if len(unassigned_faces) > 100:
        return True

    return False


def cluster_util_face_clusters_sync():
    metadata = db_get_metadata()
    if cluster_util_is_reclustering_needed(metadata):
        # Perform clustering operation
        results = cluster_util_cluster_all_face_embeddings()

        if not results:
            return 0

        results = [result.to_dict() for result in results]
        # Update database with new clusters
        db_update_face_cluster_ids_batch(results)
        # Clear old clusters
        db_delete_all_clusters()
        # Extract unique clusters with their names
        unique_clusters = {}
        for result in results:
            cluster_id = result["cluster_id"]
            cluster_name = result["cluster_name"]
            if cluster_id not in unique_clusters:
                unique_clusters[cluster_id] = {"cluster_id": cluster_id, "cluster_name": cluster_name}

        # Convert to list for batch insert
        cluster_list = list(unique_clusters.values())
        # Update the database with new clusters
        db_insert_clusters_batch(cluster_list)

        # Update metadata with new reclustering time, preserving other values
        current_metadata = metadata or {}
        current_metadata["reclustering_time"] = datetime.now().timestamp()
        db_update_metadata(current_metadata)
    else:
        face_cluster_mappings = cluster_util_assign_cluster_to_faces_without_clusterId()
        db_update_face_cluster_ids_batch(face_cluster_mappings)


def cluster_util_cluster_all_face_embeddings(eps: float = 0.3, min_samples: int = 2) -> List[ClusterResult]:
    """
    Cluster face embeddings using DBSCAN and assign cluster names based on majority voting.

    Args:
        eps: DBSCAN epsilon parameter for maximum distance between samples
        min_samples: DBSCAN minimum samples parameter for core points

    Returns:
        List of ClusterResult objects containing face_id, embedding, cluster_uuid, and cluster_name
    """
    # Get all faces with their existing cluster names
    faces_data = db_get_all_faces_with_cluster_names()

    if not faces_data:
        return []

    # Extract embeddings and face IDs
    embeddings = []
    face_ids = []
    existing_cluster_names = []

    for face in faces_data:
        face_ids.append(face["face_id"])
        embeddings.append(face["embeddings"])
        existing_cluster_names.append(face["cluster_name"])

    print(f"Total faces to cluster: {len(face_ids)}")

    # Convert to numpy array for DBSCAN
    embeddings_array = np.array(embeddings)

    # Perform DBSCAN clustering
    dbscan = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="cosine",
        n_jobs=-1,  # Use all available CPU cores
    )

    cluster_labels = dbscan.fit_predict(embeddings_array)
    print(f"DBSCAN found {len(set(cluster_labels))} clusters")

    # Group faces by cluster labels
    clusters = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        clusters[label].append(
            {"face_id": face_ids[i], "embedding": embeddings[i], "existing_cluster_name": existing_cluster_names[i]}
        )

    # Generate cluster UUIDs and determine cluster names
    results = []

    for cluster_label, faces_in_cluster in clusters.items():
        # Generate unique UUID for this cluster
        cluster_uuid = str(uuid.uuid4())

        # Determine cluster name using majority voting
        cluster_name = _determine_cluster_name(faces_in_cluster)

        # Create ClusterResult objects for all faces in this cluster
        for face in faces_in_cluster:
            result = ClusterResult(
                face_id=face["face_id"],
                embedding=face["embedding"],
                cluster_uuid=cluster_uuid,
                cluster_name=cluster_name,
            )
            results.append(result)

    return results


def cluster_util_assign_cluster_to_faces_without_clusterId(similarity_threshold: float = 0.7) -> List[Dict]:
    """
    Assign cluster IDs to faces that don't have clusters using nearest mean method with similarity threshold.

    This function:
    1. Gets all faces without cluster assignments
    2. Gets mean embeddings for existing clusters
    3. Assigns each unassigned face to the cluster with the nearest mean embedding
    4. Only assigns if similarity is above the threshold to prevent poor matches
    5. Returns the mappings without updating the database

    Args:
        similarity_threshold:
            Minimum cosine similarity required for assignment (0.0 to 1.0)
            Higher values = more strict assignment. Default: 0.7

    Returns:
        List of face-cluster mappings ready for batch update
    """
    # Get faces without cluster assignments
    unassigned_faces = db_get_faces_unassigned_clusters()

    if not unassigned_faces:
        return []

    # Get cluster mean embeddings
    cluster_means = db_get_cluster_mean_embeddings()

    if not cluster_means:
        return []

    # Prepare data for nearest neighbor assignment
    cluster_ids = []
    mean_embeddings = []

    for cluster_data in cluster_means:
        cluster_ids.append(cluster_data["cluster_id"])
        mean_embeddings.append(cluster_data["mean_embedding"])

    mean_embeddings_array = np.array(mean_embeddings)

    # Prepare batch update data
    face_cluster_mappings = []

    for face in unassigned_faces:
        face_id = face["face_id"]
        face_embedding = face["embeddings"]

        # Calculate cosine distances to all cluster means
        distances = _calculate_cosine_distances(face_embedding, mean_embeddings_array)

        # Find the best match
        min_distance = np.min(distances)
        max_similarity = 1 - min_distance

        # Only assign if similarity is above threshold
        if max_similarity >= similarity_threshold:
            nearest_cluster_idx = np.argmin(distances)
            nearest_cluster_id = cluster_ids[nearest_cluster_idx]

            face_cluster_mappings.append({"face_id": face_id, "cluster_id": nearest_cluster_id})

    return face_cluster_mappings


def _calculate_cosine_distances(face_embedding: NDArray, cluster_means: NDArray) -> NDArray:
    """
    Calculate cosine distances between a face embedding and cluster means.

    Args:
        face_embedding: Single face embedding vector
        cluster_means: Array of cluster mean embeddings (shape: [n_clusters, embedding_dim])

    Returns:
        Array of cosine distances to each cluster mean
    """
    # Normalize the face embedding
    face_norm = face_embedding / np.linalg.norm(face_embedding)

    # Normalize cluster means
    cluster_norms = cluster_means / np.linalg.norm(cluster_means, axis=1, keepdims=True)

    # Calculate cosine similarities (dot product of normalized vectors)
    cosine_similarities = np.dot(cluster_norms, face_norm)

    # Convert to cosine distances (1 - similarity)
    cosine_distances = 1 - cosine_similarities

    return cosine_distances


def _determine_cluster_name(faces_in_cluster: List[Dict]) -> Optional[str]:
    """
    Determine cluster name using majority voting from existing cluster names.

    Args:
        faces_in_cluster: List of face dictionaries containing existing_cluster_name

    Returns:
        Most common non-null cluster name, or None if no named clusters exist
    """
    # Extract non-null cluster names
    existing_names = [
        face["existing_cluster_name"] for face in faces_in_cluster if face["existing_cluster_name"] is not None
    ]

    if not existing_names:
        return None

    # Use Counter to find the most common name
    name_counts = Counter(existing_names)
    most_common_name, _ = name_counts.most_common(1)[0]

    return most_common_name
