import numpy as np
import uuid
import json
import base64
import cv2
import sqlite3
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics.pairwise import cosine_similarity


from collections import defaultdict, Counter
from typing import List, Dict, Optional, Union
from numpy.typing import NDArray
from app.database.connection import get_db_connection

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
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class ClusterResult:
    """Result class for clustering operation"""

    def __init__(
        self,
        face_id: int,
        embedding: NDArray,
        cluster_uuid: str,
        cluster_name: Optional[str],
    ):
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


def cluster_util_face_clusters_sync(force_full_reclustering: bool = False):
    """
    Smart face clustering with transaction safety.
    Decides between full reclustering or incremental assignment based on 24-hour rule and face count.

    Args:
        force_full_reclustering: If True, forces full reclustering regardless of 24-hour rule
    """
    metadata = db_get_metadata()
    if force_full_reclustering or cluster_util_is_reclustering_needed(metadata):
        # Perform clustering operation
        results = cluster_util_cluster_all_face_embeddings()

        if not results:
            return 0

        results = [result.to_dict() for result in results]

        # Extract unique clusters with their names (without face images yet)
        unique_clusters = {}
        for result in results:
            cluster_id = result["cluster_id"]
            cluster_name = result["cluster_name"]
            if cluster_id not in unique_clusters:
                unique_clusters[cluster_id] = {
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "face_image_base64": None,  # Will be updated later
                }

        # Convert to list for batch insert
        cluster_list = list(unique_clusters.values())

        # Perform all database operations within a single transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Clear old clusters first
            db_delete_all_clusters(cursor)

            # Insert the new clusters into database first
            db_insert_clusters_batch(cluster_list, cursor)

            # Now update face cluster assignments (foreign keys will be valid)
            db_update_face_cluster_ids_batch(results, cursor)

            # Finally, generate and update face images for each cluster
            for cluster_id in unique_clusters.keys():
                face_image_base64 = _generate_cluster_face_image(cluster_id, cursor)
                if face_image_base64:
                    # Update the cluster with the generated face image
                    success = _update_cluster_face_image(
                        cluster_id, face_image_base64, cursor
                    )
                    if not success:
                        raise RuntimeError(
                            f"Failed to update face image for cluster {cluster_id}"
                        )

            # Update metadata with new reclustering time, preserving other values
            current_metadata = metadata or {}
            current_metadata["reclustering_time"] = datetime.now().timestamp()
            db_update_metadata(current_metadata, cursor)
        return len(cluster_list)
    else:
        face_cluster_mappings = cluster_util_assign_cluster_to_faces_without_clusterId()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            db_update_face_cluster_ids_batch(face_cluster_mappings, cursor)
        return len(face_cluster_mappings)


def _validate_embedding(embedding: NDArray, min_norm: float = 1e-6) -> bool:
    """
    Validate that an embedding is usable for distance calculations.

    Args:
        embedding: Face embedding vector to validate
        min_norm: Minimum acceptable L2 norm for the embedding

    Returns:
        True if embedding is valid, False otherwise
    """
    # Check for NaN or infinite values
    if not np.isfinite(embedding).all():
        return False

    # Check if embedding is effectively zero (too small norm)
    norm = np.linalg.norm(embedding)
    if norm < min_norm:
        return False

    return True


def cluster_util_cluster_all_face_embeddings(
    eps: float = 0.75,
    min_samples: int = 2,
    similarity_threshold: float = 0.85,
    merge_threshold: float = None,
) -> List[ClusterResult]:
    """
    Cluster face embeddings using DBSCAN with similarity validation.

    Args:
        eps: DBSCAN epsilon parameter for maximum distance between samples (default: 0.75)
        min_samples: DBSCAN minimum samples parameter for core points (default: 2)
        similarity_threshold: Minimum similarity to consider same person (default: 0.85, range: 0.75-0.90)
        merge_threshold: Similarity threshold for post-clustering merge (default: None, uses similarity_threshold)

    Returns:
        List of ClusterResult objects containing face_id, embedding, cluster_uuid, and cluster_name
    """
    # Get all faces with their existing cluster names
    faces_data = db_get_all_faces_with_cluster_names()

    if not faces_data:
        return []

    # Extract embeddings and face IDs with validation
    embeddings = []
    face_ids = []
    existing_cluster_names = []
    invalid_count = 0

    for face in faces_data:
        embedding = face["embeddings"]

        # Validate embedding before adding
        if _validate_embedding(embedding):
            face_ids.append(face["face_id"])
            embeddings.append(embedding)
            existing_cluster_names.append(face["cluster_name"])
        else:
            invalid_count += 1
            logger.warning(
                f"Skipping invalid embedding for face_id {face['face_id']} (NaN or zero vector)"
            )

    if invalid_count > 0:
        logger.warning(f"Filtered out {invalid_count} invalid embeddings")

    if not embeddings:
        logger.error("No valid embeddings found after validation")
        return []

    logger.info(f"Total valid faces to cluster: {len(face_ids)}")

    # Convert to numpy array for DBSCAN
    embeddings_array = np.array(embeddings)

    # Calculate pairwise distances with similarity threshold
    distances = cosine_distances(embeddings_array)

    # Guard against NaN distances (shouldn't happen after validation, but double-check)
    if not np.isfinite(distances).all():
        logger.error(
            "NaN or infinite values detected in distance matrix after validation"
        )
        # Replace NaN/inf with max distance (1.0)
        distances = np.nan_to_num(distances, nan=1.0, posinf=1.0, neginf=1.0)

    # Apply similarity threshold - mark dissimilar faces as completely different
    max_distance = 1 - similarity_threshold  # Convert similarity to distance
    distances[distances > max_distance] = 1.0  # Mark as completely different
    logger.info(
        f"Applied similarity threshold: {similarity_threshold} (max_distance: {max_distance:.3f})"
    )

    # Perform DBSCAN clustering with precomputed distances
    dbscan = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="precomputed",
        n_jobs=-1,  # Use all available CPU cores
    )

    cluster_labels = dbscan.fit_predict(distances)
    logger.info(
        f"DBSCAN found {len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)} clusters"
    )

    # Group faces by cluster labels
    clusters = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        # Ignore noise points (label -1)
        if label != -1:
            clusters[label].append(
                {
                    "face_id": face_ids[i],
                    "embedding": embeddings[i],
                    "existing_cluster_name": existing_cluster_names[i],
                }
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

    # Post-clustering merge: merge similar clusters based on representative faces
    # Use similarity_threshold if merge_threshold not explicitly provided
    effective_merge_threshold = merge_threshold if merge_threshold is not None else 0.7
    results = _merge_similar_clusters(
        results, merge_threshold=effective_merge_threshold
    )

    return results


def cluster_util_assign_cluster_to_faces_without_clusterId(
    similarity_threshold: float = 0.8,
) -> List[Dict]:
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

    # Prepare data for nearest neighbor assignment with validation
    cluster_ids = []
    mean_embeddings = []
    invalid_clusters = 0

    for cluster_data in cluster_means:
        mean_emb = cluster_data["mean_embedding"]

        # Validate cluster mean embedding
        if _validate_embedding(mean_emb):
            cluster_ids.append(cluster_data["cluster_id"])
            mean_embeddings.append(mean_emb)
        else:
            invalid_clusters += 1
            logger.warning(
                f"Skipping invalid cluster mean for cluster_id {cluster_data['cluster_id']}"
            )

    if invalid_clusters > 0:
        logger.warning(f"Filtered out {invalid_clusters} invalid cluster means")

    if not mean_embeddings:
        logger.error("No valid cluster means found after validation")
        return []

    mean_embeddings_array = np.array(mean_embeddings)

    # Prepare batch update data
    face_cluster_mappings = []
    skipped_invalid = 0

    for face in unassigned_faces:
        face_id = face["face_id"]
        face_embedding = face["embeddings"]

        # Validate face embedding
        if not _validate_embedding(face_embedding):
            skipped_invalid += 1
            logger.warning(f"Skipping face_id {face_id} with invalid embedding")
            continue

        # Calculate cosine distances to all cluster means
        distances = _calculate_cosine_distances(face_embedding, mean_embeddings_array)

        # Guard against NaN distances
        if not np.isfinite(distances).all():
            logger.warning(f"NaN distances for face_id {face_id}, skipping")
            skipped_invalid += 1
            continue

        # Find the best match
        min_distance = np.min(distances)
        max_similarity = 1 - min_distance

        # Only assign if similarity is above threshold
        if max_similarity >= similarity_threshold:
            nearest_cluster_idx = np.argmin(distances)
            nearest_cluster_id = cluster_ids[nearest_cluster_idx]

            face_cluster_mappings.append(
                {"face_id": face_id, "cluster_id": nearest_cluster_id}
            )

    if skipped_invalid > 0:
        logger.warning(
            f"Skipped {skipped_invalid} faces with invalid embeddings during assignment"
        )

    return face_cluster_mappings


def _merge_similar_clusters(
    results: List[ClusterResult], merge_threshold: float = 0.85
) -> List[ClusterResult]:
    """
    Merge clusters that are too similar based on their mean embeddings.

    Args:
        results: List of ClusterResult objects
        merge_threshold: Similarity threshold for merging (default: 0.85)

    Returns:
        Updated list with merged clusters
    """
    if not results:
        return results

    # Group faces by cluster
    cluster_map = defaultdict(list)
    for result in results:
        cluster_map[result.cluster_uuid].append(result)

    if len(cluster_map) <= 1:
        return results  # Nothing to merge

    # Calculate mean embedding for each cluster with validation
    cluster_means = {}
    invalid_clusters = []

    for cluster_uuid, cluster_faces in cluster_map.items():
        embeddings = np.array([face.embedding for face in cluster_faces])
        mean_embedding = np.mean(embeddings, axis=0)

        # Validate cluster mean
        if _validate_embedding(mean_embedding):
            cluster_means[cluster_uuid] = mean_embedding
        else:
            invalid_clusters.append(cluster_uuid)
            logger.warning(
                f"Cluster {cluster_uuid} has invalid mean embedding, excluding from merge"
            )

    # Remove invalid clusters from consideration
    for invalid_uuid in invalid_clusters:
        cluster_map.pop(invalid_uuid, None)

    if len(cluster_means) <= 1:
        return results  # Not enough valid clusters to merge

    # Find clusters to merge based on similarity
    cluster_uuids = list(cluster_means.keys())
    merge_mapping = {}  # Maps old cluster_uuid -> new cluster_uuid

    for i, uuid1 in enumerate(cluster_uuids):
        if uuid1 in merge_mapping:
            continue  # Already merged

        for j in range(i + 1, len(cluster_uuids)):
            uuid2 = cluster_uuids[j]
            if uuid2 in merge_mapping:
                continue  # Already merged

            # Calculate similarity between cluster means
            emb1 = cluster_means[uuid1].reshape(1, -1)
            emb2 = cluster_means[uuid2].reshape(1, -1)

            similarity = cosine_similarity(emb1, emb2)[0][0]

            # Guard against NaN similarity
            if not np.isfinite(similarity):
                logger.warning(
                    f"NaN similarity between clusters {uuid1} and {uuid2}, skipping merge"
                )
                continue

            # If very similar, merge cluster2 into cluster1
            if similarity >= merge_threshold:
                merge_mapping[uuid2] = uuid1
                logger.info(
                    f"Merging cluster {uuid2} into {uuid1} (similarity: {similarity:.3f})"
                )

    # Apply merges
    if merge_mapping:
        # Resolve transitive merges (follow chain to ultimate target)
        def resolve_final_cluster(uuid):
            visited = set()
            current = uuid
            while current in merge_mapping and current not in visited:
                visited.add(current)
                current = merge_mapping[current]
            return current

        # Build merged results with resolved cluster UUIDs
        merged_results = []
        for result in results:
            final_cluster = resolve_final_cluster(result.cluster_uuid)

            # Create new result with updated cluster_uuid (name will be updated next)
            merged_result = ClusterResult(
                face_id=result.face_id,
                embedding=result.embedding,
                cluster_uuid=final_cluster,
                cluster_name=result.cluster_name,  # Original name, will be updated
            )
            merged_results.append(merged_result)

        # Compute final cluster names by majority vote
        cluster_name_votes = defaultdict(list)
        for result in merged_results:
            if result.cluster_name:  # Only count non-None names
                cluster_name_votes[result.cluster_uuid].append(result.cluster_name)

        # Determine final name for each cluster
        final_cluster_names = {}
        for cluster_uuid, names in cluster_name_votes.items():
            if names:
                # Majority vote: most common name wins
                name_counts = Counter(names)
                final_name = name_counts.most_common(1)[0][0]
                final_cluster_names[cluster_uuid] = final_name
            else:
                final_cluster_names[cluster_uuid] = None

        # Update all results with final cluster names
        for result in merged_results:
            result.cluster_name = final_cluster_names.get(result.cluster_uuid)

        logger.info(
            f"Merged {len(merge_mapping)} clusters. Final count: {len(set(r.cluster_uuid for r in merged_results))}"
        )
        return merged_results

    return results


def _calculate_cosine_distances(
    face_embedding: NDArray, cluster_means: NDArray
) -> NDArray:
    """
    Calculate cosine distances between a face embedding and cluster means.
    Handles edge cases with zero vectors and ensures finite results.

    Args:
        face_embedding: Single face embedding vector
        cluster_means: Array of cluster mean embeddings (shape: [n_clusters, embedding_dim])

    Returns:
        Array of cosine distances to each cluster mean
    """
    # Normalize the face embedding with safe division
    face_norm_value = np.linalg.norm(face_embedding)
    if face_norm_value < 1e-6:
        # Zero vector, return maximum distance to all clusters
        return np.ones(len(cluster_means))
    face_norm = face_embedding / face_norm_value

    # Normalize cluster means with safe division
    cluster_norm_values = np.linalg.norm(cluster_means, axis=1, keepdims=True)
    cluster_norm_values = np.maximum(
        cluster_norm_values, 1e-6
    )  # Prevent division by zero
    cluster_norms = cluster_means / cluster_norm_values

    # Calculate cosine similarities (dot product of normalized vectors)
    cosine_similarities = np.dot(cluster_norms, face_norm)

    # Convert to cosine distances (1 - similarity)
    cosine_distances = 1 - cosine_similarities

    # Guard against numerical errors producing values outside [0, 2]
    cosine_distances = np.clip(cosine_distances, 0.0, 2.0)

    return cosine_distances


def _update_cluster_face_image(
    cluster_id: str, face_image_base64: str, cursor: Optional[sqlite3.Cursor] = None
) -> bool:
    """
    Update the face image for a specific cluster.

    Args:
        cluster_id: The UUID of the cluster
        face_image_base64: Base64 encoded face image string
        cursor: Optional existing database cursor. If None, creates a new connection.

    Returns:
        True if update was successful, False otherwise
    """
    own_connection = cursor is None
    if own_connection:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE face_clusters SET face_image_base64 = ? WHERE cluster_id = ?",
            (face_image_base64, cluster_id),
        )
        success = cursor.rowcount > 0
        if own_connection:
            conn.commit()
        return success
    except Exception as e:
        logger.error(f"Error updating face image for cluster {cluster_id}: {e}")
        if own_connection:
            conn.rollback()
            return False

        raise
    finally:
        if own_connection:
            conn.close()


def _get_cluster_face_data(
    cluster_uuid: str, cursor: sqlite3.Cursor
) -> Optional[tuple]:
    """
    Get the image path and bounding box for the first face in a cluster.

    Args:
        cluster_uuid: The UUID of the cluster
        cursor: SQLite cursor from an active transaction

    Returns:
        Tuple of (image_path, bbox_dict) or None if not found
    """
    try:
        cursor.execute(
            """
            SELECT i.path, f.bbox
            FROM faces f
            JOIN images i ON f.image_id = i.id
            WHERE f.cluster_id = ?
            LIMIT 1
            """,
            (cluster_uuid,),
        )

        face_data = cursor.fetchone()
        if not face_data:
            return None

        image_path, bbox_json = face_data

        if not bbox_json or not image_path:
            return None

        try:
            bbox = json.loads(bbox_json)
            return (image_path, bbox)
        except json.JSONDecodeError:
            return None

    except Exception as e:
        logger.error(f"Error getting face data for cluster {cluster_uuid}: {e}")
        return None


def _calculate_square_crop_bounds(
    bbox: Dict, img_shape: tuple, padding: int = 50
) -> tuple:
    """
    Calculate square crop bounds centered on a face bounding box.

    Args:
        bbox: Dictionary with x, y, width, height keys
        img_shape: Tuple of (height, width, channels) from image
        padding: Padding around the face in pixels

    Returns:
        Tuple of (x_start, y_start, x_end, y_end) for square crop
    """
    img_height, img_width = img_shape[:2]

    x = int(bbox.get("x", 0))
    y = int(bbox.get("y", 0))
    width = int(bbox.get("width", 100))
    height = int(bbox.get("height", 100))

    # Add padding around the face
    x_start = max(0, x - padding)
    y_start = max(0, y - padding)
    x_end = min(img_width, x + width + padding)
    y_end = min(img_height, y + height + padding)

    # Calculate square crop dimensions centered on the face
    crop_width = x_end - x_start
    crop_height = y_end - y_start

    # Use the larger dimension to create a square crop
    square_size = max(crop_width, crop_height)

    # Calculate center of the current crop
    center_x = x_start + crop_width // 2
    center_y = y_start + crop_height // 2

    # Calculate square crop bounds centered on the face
    half_square = square_size // 2
    square_x_start = max(0, center_x - half_square)
    square_y_start = max(0, center_y - half_square)
    square_x_end = min(img_width, center_x + half_square)
    square_y_end = min(img_height, center_y + half_square)

    # Adjust if we hit image boundaries to maintain square shape
    actual_width = square_x_end - square_x_start
    actual_height = square_y_end - square_y_start
    actual_square_size = min(actual_width, actual_height)

    # Recalculate final square crop
    square_x_start = center_x - actual_square_size // 2
    square_y_start = center_y - actual_square_size // 2
    square_x_end = square_x_start + actual_square_size
    square_y_end = square_y_start + actual_square_size

    # Ensure bounds are within image
    square_x_start = max(0, square_x_start)
    square_y_start = max(0, square_y_start)
    square_x_end = min(img_width, square_x_end)
    square_y_end = min(img_height, square_y_end)

    return (square_x_start, square_y_start, square_x_end, square_y_end)


def _crop_and_resize_face(
    img: np.ndarray, crop_bounds: tuple, target_size: int = 300
) -> Optional[np.ndarray]:
    """
    Crop and resize a face region from an image.

    Args:
        img: Input image as numpy array
        crop_bounds: Tuple of (x_start, y_start, x_end, y_end)
        target_size: Target size for the output square image

    Returns:
        Cropped and resized face image or None if cropping fails
    """
    try:
        x_start, y_start, x_end, y_end = crop_bounds

        # Crop the square region
        face_crop = img[y_start:y_end, x_start:x_end]

        # Check if crop is valid
        if face_crop.size == 0:
            return None

        # Resize to target size (maintaining square aspect ratio)
        face_crop = cv2.resize(face_crop, (target_size, target_size))

        return face_crop
    except Exception as e:
        logger.error(f"Error cropping and resizing face: {e}")
        return None


def _encode_image_to_base64(img: np.ndarray, format: str = ".jpg") -> Optional[str]:
    """
    Encode an image to base64 string.

    Args:
        img: Image as numpy array
        format: Image format for encoding (e.g., ".jpg", ".png")

    Returns:
        Base64 encoded string or None if encoding fails
    """
    try:
        _, buffer = cv2.imencode(format, img)
        return base64.b64encode(buffer).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        return None


def _generate_cluster_face_image(
    cluster_uuid: str, cursor: sqlite3.Cursor
) -> Optional[str]:
    """
    Generate a base64 encoded face image for a cluster.

    Args:
        cluster_uuid: The UUID of the cluster
        cursor: SQLite cursor from an active transaction

    Returns:
        Base64 encoded face image string, or None if generation fails
    """
    try:
        # Get face data from database
        face_data = _get_cluster_face_data(cluster_uuid, cursor)
        if not face_data:
            return None

        image_path, bbox = face_data

        # Load the image
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Calculate square crop bounds
        crop_bounds = _calculate_square_crop_bounds(bbox, img.shape)

        # Crop and resize the face
        face_crop = _crop_and_resize_face(img, crop_bounds)
        if face_crop is None:
            return None

        # Encode to base64
        return _encode_image_to_base64(face_crop)

    except Exception as e:
        logger.error(f"Error generating face image for cluster {cluster_uuid}: {e}")
        return None


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
        face["existing_cluster_name"]
        for face in faces_in_cluster
        if face["existing_cluster_name"] is not None
    ]

    if not existing_names:
        return None

    # Use Counter to find the most common name
    name_counts = Counter(existing_names)
    most_common_name, _ = name_counts.most_common(1)[0]

    return most_common_name
