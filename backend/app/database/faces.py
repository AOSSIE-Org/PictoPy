import sqlite3
import json
import numpy as np
from typing import Optional, List, Dict, Union, TypedDict, Any
from app.config.settings import DATABASE_PATH

# Type definitions
FaceId = int
ImageId = str
ClusterId = int
BoundingBox = Dict[str, Union[int, float]]
FaceEmbedding = np.ndarray


class FaceData(TypedDict):
    """Represents the full faces table structure"""

    face_id: FaceId
    image_id: ImageId
    cluster_id: Optional[ClusterId]
    embeddings: FaceEmbedding  # Numpy array in application, stored as JSON string in DB
    confidence: Optional[float]
    bbox: Optional[BoundingBox]


FaceClusterMapping = Dict[FaceId, Optional[ClusterId]]


def db_create_faces_table() -> None:
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS faces (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT,
                cluster_id INTEGER,
                embeddings TEXT,
                confidence REAL,
                bbox TEXT,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (cluster_id) REFERENCES face_clusters(cluster_id) ON DELETE SET NULL
            )
        """
        )
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def db_insert_face_embeddings(
    image_id: ImageId,
    embeddings: FaceEmbedding,
    confidence: Optional[float] = None,
    bbox: Optional[BoundingBox] = None,
    cluster_id: Optional[ClusterId] = None,
) -> Optional[FaceId]:
    """
    Insert face embeddings with additional metadata.


    Args:
        image_id: ID of the image this face belongs to
        embeddings: Face embedding vector (numpy array)
        confidence: Confidence score for face detection (optional)
        bbox: Bounding box coordinates as dict with keys: x, y, width, height (optional)
        cluster_id: ID of the face cluster this face belongs to (optional)

    Returns:
        FaceId if successful, None if insert failed
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        embeddings_json = json.dumps(embeddings.tolist())

        # Convert bbox to JSON string if provided
        bbox_json = json.dumps(bbox) if bbox is not None else None

        cursor.execute(
            """
            INSERT INTO faces (image_id, cluster_id, embeddings, confidence, bbox)
            VALUES (?, ?, ?, ?, ?)
        """,
            (image_id, cluster_id, embeddings_json, confidence, bbox_json),
        )

        face_id = cursor.lastrowid
        conn.commit()
        return face_id
    finally:
        conn.close()


def db_insert_face_embeddings_by_image_id(
    image_id: ImageId,
    embeddings: Union[FaceEmbedding, List[FaceEmbedding]],
    confidence: Optional[Union[float, List[float]]] = None,
    bbox: Optional[Union[BoundingBox, List[BoundingBox]]] = None,
    cluster_id: Optional[Union[ClusterId, List[ClusterId]]] = None,
) -> Union[Optional[FaceId], List[Optional[FaceId]]]:
    """
    Insert face embeddings using image path (convenience function).

    Args:
        image_id: Image ID (uuid string)
        embeddings: Face embedding vector (numpy array) or list of embeddings
        confidence: Confidence score(s) for face detection (optional)
        bbox: Bounding box coordinates or list of bounding boxes (optional)
        cluster_id: Cluster ID(s) for the face(s) (optional)

    Returns:
        FaceId or list of FaceIds. Can be None if insert failed.
    """

    # Handle multiple faces in one image
    if (
        isinstance(embeddings, list)
        and len(embeddings) > 0
        and isinstance(embeddings[0], np.ndarray)
    ):
        face_ids: List[Optional[FaceId]] = []
        for i, emb in enumerate(embeddings):
            # Extract single confidence value
            conf: Optional[float] = None
            if isinstance(confidence, list) and i < len(confidence):
                conf = confidence[i]
            elif isinstance(confidence, (int, float)):
                conf = float(confidence)

            # Extract single bbox value
            bb: Optional[BoundingBox] = None
            if isinstance(bbox, list) and i < len(bbox):
                bb = bbox[i]
            elif isinstance(bbox, dict):
                bb = bbox

            # Extract single cluster_id value
            cid: Optional[ClusterId] = None
            if isinstance(cluster_id, list) and i < len(cluster_id):
                cid = cluster_id[i]
            elif isinstance(cluster_id, int):
                cid = cluster_id

            face_id = db_insert_face_embeddings(image_id, emb, conf, bb, cid)
            face_ids.append(face_id)
        return face_ids
    else:
        # Single face - extract single values from potential lists
        single_conf: Optional[float] = None
        if isinstance(confidence, list) and len(confidence) > 0:
            single_conf = confidence[0]
        elif isinstance(confidence, (int, float)):
            single_conf = float(confidence)

        single_bbox: Optional[BoundingBox] = None
        if isinstance(bbox, list) and len(bbox) > 0:
            single_bbox = bbox[0]
        elif isinstance(bbox, dict):
            single_bbox = bbox

        single_cid: Optional[ClusterId] = None
        if isinstance(cluster_id, list) and len(cluster_id) > 0:
            single_cid = cluster_id[0]
        elif isinstance(cluster_id, int):
            single_cid = cluster_id

        return db_insert_face_embeddings(
            image_id, embeddings, single_conf, single_bbox, single_cid
        )


def get_all_face_embeddings() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                f.embeddings,
                f.bbox,
                i.id,
                i.path,
                i.folder_id,
                i.thumbnailPath,
                i.metadata,
                i.isTagged,
                m.name as tag_name
            FROM faces f
            JOIN images i ON f.image_id=i.id
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
        """
        )
        results = cursor.fetchall()

        from app.utils.images import image_util_parse_metadata

        images_dict: Dict[str, Dict[str, Any]] = {}
        for (
            embeddings,
            bbox,
            image_id,
            path,
            folder_id,
            thumbnail_path,
            metadata,
            is_tagged,
            tag_name,
        ) in results:
            if image_id not in images_dict:
                try:
                    embeddings_json = json.loads(embeddings) if embeddings else None
                    bbox_json = json.loads(bbox) if bbox else None
                except json.JSONDecodeError:
                    continue
                images_dict[image_id] = {
                    "embeddings": embeddings_json,
                    "bbox": bbox_json,
                    "id": image_id,
                    "path": path,
                    "folder_id": folder_id,
                    "thumbnailPath": thumbnail_path,
                    "metadata": image_util_parse_metadata(metadata),
                    "isTagged": bool(is_tagged),
                    "tags": [],
                }

            # Add tag if it exists
            if tag_name:
                images_dict[image_id]["tags"].append(tag_name)

        # Convert to list and set tags to None if empty
        images: List[Dict[str, Any]] = []
        for image_data in images_dict.values():
            if not image_data["tags"]:
                image_data["tags"] = None
            images.append(image_data)

        # Sort by path
        images.sort(key=lambda x: x["path"])
        return images
    finally:
        conn.close()


def db_get_faces_unassigned_clusters() -> List[Dict[str, Union[FaceId, FaceEmbedding]]]:
    """
    Get all faces that don't have assigned clusters.

    Returns:
        List of dictionaries containing face_id and embeddings (as numpy array)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT face_id, embeddings FROM faces WHERE cluster_id IS NULL")

        rows = cursor.fetchall()

        faces: List[Dict[str, Union[FaceId, FaceEmbedding]]] = []
        for row in rows:
            face_id, embeddings_json = row
            # Convert JSON string back to numpy array
            embeddings = np.array(json.loads(embeddings_json))
            faces.append({"face_id": face_id, "embeddings": embeddings})

        return faces
    finally:
        conn.close()


def db_get_all_faces_with_cluster_names() -> (
    List[Dict[str, Union[FaceId, FaceEmbedding, Optional[str]]]]
):
    """
    Get all faces with their corresponding cluster names.

    Returns:
        List of dictionaries containing face_id, embeddings (as numpy array), and cluster_name
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT f.face_id, f.embeddings, fc.cluster_name
            FROM faces f
            LEFT JOIN face_clusters fc ON f.cluster_id = fc.cluster_id
            ORDER BY f.face_id
            """
        )

        rows = cursor.fetchall()

        faces: List[Dict[str, Union[FaceId, FaceEmbedding, Optional[str]]]] = []
        for row in rows:
            face_id, embeddings_json, cluster_name = row
            # Convert JSON string back to numpy array
            embeddings = np.array(json.loads(embeddings_json))
            faces.append(
                {
                    "face_id": face_id,
                    "embeddings": embeddings,
                    "cluster_name": cluster_name,
                }
            )

        return faces
    finally:
        conn.close()


def db_update_face_cluster_ids_batch(
    face_cluster_mapping: List[Dict[str, Union[FaceId, ClusterId, None]]],
    cursor: Optional[sqlite3.Cursor] = None,
) -> None:
    """
    Update cluster IDs for multiple faces in batch.

    Args:
        face_cluster_mapping: List of dictionaries containing face_id and cluster_id pairs
                             Each dict should have keys: 'face_id' and 'cluster_id'
        cursor: Optional existing database cursor. If None, creates a new connection.

    Example:
        face_cluster_mapping = [
            {'face_id': 1, 'cluster_id': 1},
            {'face_id': 2, 'cluster_id': 2},
            {'face_id': 3, 'cluster_id': None}  # To unassign cluster
        ]
    """
    if not face_cluster_mapping:
        return

    conn = None
    own_connection = cursor is None
    
    if own_connection:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

    # At this point cursor should never be None
    if cursor is None:
        raise ValueError("Database cursor is required")

    try:
        # Prepare update data as tuples (cluster_id, face_id)
        update_data: List[tuple] = []
        for mapping in face_cluster_mapping:
            face_id = mapping.get("face_id")
            cluster_id = mapping.get("cluster_id")
            update_data.append((cluster_id, face_id))

        cursor.executemany(
            """
            UPDATE faces
            SET cluster_id = ?
            WHERE face_id = ?
            """,
            update_data,
        )

        if own_connection and conn:
            conn.commit()
    except Exception:
        if own_connection and conn:
            conn.rollback()
        print("Error updating face cluster IDs in batch.")
        raise
    finally:
        if own_connection and conn:
            conn.close()


def db_get_cluster_mean_embeddings() -> List[Dict[str, Union[int, FaceEmbedding]]]:
    """
    Get cluster IDs and their corresponding mean face embeddings.

    Returns:
        List of dictionaries containing cluster_id and mean_embedding (as numpy array)
        Only returns clusters that have at least one face assigned
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT f.cluster_id, f.embeddings
            FROM faces f
            WHERE f.cluster_id IS NOT NULL
            ORDER BY f.cluster_id
            """
        )

        rows = cursor.fetchall()

        if not rows:
            return []

        # Group embeddings by cluster_id
        cluster_embeddings: Dict[int, List[np.ndarray]] = {}
        for row in rows:
            cluster_id, embeddings_json = row
            # Convert JSON string back to numpy array
            embeddings = np.array(json.loads(embeddings_json))

            if cluster_id not in cluster_embeddings:
                cluster_embeddings[cluster_id] = []
            cluster_embeddings[cluster_id].append(embeddings)

        # Calculate mean embeddings for each cluster
        cluster_means: List[Dict[str, Union[int, FaceEmbedding]]] = []
        for cluster_id, embeddings_list in cluster_embeddings.items():
            # Stack all embeddings for this cluster and calculate mean
            stacked_embeddings = np.stack(embeddings_list)
            mean_embedding = np.mean(stacked_embeddings, axis=0)

            cluster_means.append(
                {"cluster_id": cluster_id, "mean_embedding": mean_embedding}
            )

        return cluster_means
    finally:
        conn.close()