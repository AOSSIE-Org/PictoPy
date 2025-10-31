import numpy as np
import uuid
import json
import base64
import cv2
import sqlite3
from datetime import datetime
from sklearn.cluster import DBSCAN
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Union, Tuple
from numpy.typing import NDArray
from contextlib import contextmanager

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


@contextmanager
def get_db_transaction() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    Context manager that provides a database connection and cursor with transaction management.
    Automatically commits on success or rolls back on error.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
        with get_db_transaction() as (conn, cursor):
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
    else:
        face_cluster_mappings = cluster_util_assign_cluster_to_faces_without_clusterId()
        with get_db_transaction() as (conn, cursor):
            db_update_face_cluster_ids_batch(face_cluster_mappings, cursor)


def cluster_util_cluster_all_face_embeddings(
    eps: float = 0.3, min_samples: int = 2
) -> List[ClusterResult]:
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

    logger.info(f"Total faces to cluster: {len(face_ids)}")

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
    logger.info(f"DBSCAN found {len(set(cluster_labels)) - 1} clusters")

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

    return results


def cluster_util_assign_cluster_to_faces_without_clusterId(
    similarity_threshold: float = 0.7,
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

            face_cluster_mappings.append(
                {"face_id": face_id, "cluster_id": nearest_cluster_id}
            )

    return face_cluster_mappings


def _calculate_cosine_distances(
    face_embedding: NDArray, cluster_means: NDArray
) -> NDArray:
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
