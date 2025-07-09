import sqlite3
import json
import numpy as np
from typing import Optional, List, Dict, Union, TypedDict
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
    embeddings: FaceEmbedding
    confidence: Optional[float]
    bbox: Optional[BoundingBox]


FaceClusterMapping = Dict[FaceId, Optional[ClusterId]]


def db_create_faces_table() -> None:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faces (
            face_id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id INTEGER,
            cluster_id INTEGER,
            embeddings BLOB,
            confidence REAL,
            bbox TEXT,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        )
    """
    )
    conn.commit()
    conn.close()


def db_insert_face_embeddings(
    image_id: ImageId,
    embeddings: FaceEmbedding,
    confidence: Optional[float] = None,
    bbox: Optional[BoundingBox] = None,
    cluster_id: Optional[ClusterId] = None,
) -> FaceId:
    """
    Insert face embeddings with additional metadata.


    Args:
        image_id: ID of the image this face belongs to
        embeddings: Face embedding vector (numpy array)
        confidence: Confidence score for face detection (optional)
        bbox: Bounding box coordinates as dict with keys: x, y, width, height (optional)
        cluster_id: ID of the face cluster this face belongs to (optional)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Convert embeddings to bytes for BLOB storage
    embeddings_blob = embeddings.tobytes()

    # Convert bbox to JSON string if provided
    bbox_json = json.dumps(bbox) if bbox is not None else None

    cursor.execute(
        """
        INSERT INTO faces (image_id, cluster_id, embeddings, confidence, bbox)
        VALUES (?, ?, ?, ?, ?)
    """,
        (image_id, cluster_id, embeddings_blob, confidence, bbox_json),
    )

    face_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return face_id


def db_insert_face_embeddings_by_path(
    image_path: str,
    embeddings: Union[FaceEmbedding, List[FaceEmbedding]],
    confidence: Optional[Union[float, List[float]]] = None,
    bbox: Optional[Union[BoundingBox, List[BoundingBox]]] = None,
    cluster_id: Optional[Union[ClusterId, List[ClusterId]]] = None,
) -> Union[FaceId, List[FaceId]]:
    """
    Insert face embeddings using image path (convenience function).

    Args:
        image_path: Path to the image file
        embeddings: Face embedding vector (numpy array) or list of embeddings
        confidence: Confidence score(s) for face detection (optional)
        bbox: Bounding box coordinates or list of bounding boxes (optional)
        cluster_id: Cluster ID(s) for the face(s) (optional)
    """
    from app.utils.path_id_mapping import get_id_from_path

    image_id = get_id_from_path(image_path)
    if image_id is None:
        raise ValueError(f"Image '{image_path}' not found in the database")

    # Handle multiple faces in one image
    if isinstance(embeddings, list) and len(embeddings) > 0 and isinstance(embeddings[0], np.ndarray):
        face_ids = []
        for i, emb in enumerate(embeddings):
            conf = confidence[i] if isinstance(confidence, list) and i < len(confidence) else confidence
            bb = bbox[i] if isinstance(bbox, list) and i < len(bbox) else bbox
            cid = cluster_id[i] if isinstance(cluster_id, list) and i < len(cluster_id) else cluster_id
            face_id = db_insert_face_embeddings(image_id, emb, conf, bb, cid)
            face_ids.append(face_id)
        return face_ids
    else:
        # Single face
        return db_insert_face_embeddings(image_id, embeddings, confidence, bbox, cluster_id)


def db_get_face_embeddings_by_path(image_path: str) -> Optional[List[FaceData]]:
    """
    Get face embeddings and metadata for an image by path.

    Returns:
        List of dictionaries containing face data: face_id, embeddings, confidence, bbox, cluster_id
    """
    from app.utils.path_id_mapping import get_id_from_path

    image_id = get_id_from_path(image_path)
    if image_id is None:
        return None

    return db_get_face_embeddings_by_image_id(image_id)


def db_get_face_embeddings_by_image_id(image_id: ImageId) -> Optional[List[FaceData]]:
    """
    Get face embeddings and metadata for an image by image_id.

    Returns:
        List of dictionaries containing face data: face_id, embeddings, confidence, bbox, cluster_id
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT face_id, embeddings, confidence, bbox, cluster_id FROM faces
        WHERE image_id = ?
    """,
        (image_id,),
    )

    results = cursor.fetchall()
    conn.close()

    faces = []
    for face_id, embeddings_blob, confidence, bbox_json, cluster_id in results:
        # Convert BLOB back to numpy array
        embeddings = np.frombuffer(embeddings_blob, dtype=np.float64)

        # Parse bbox JSON if present
        bbox = json.loads(bbox_json) if bbox_json else None

        faces.append(
            {
                "face_id": face_id,
                "embeddings": embeddings,
                "confidence": confidence,
                "bbox": bbox,
                "cluster_id": cluster_id,
            }
        )

    return faces if faces else None


def db_get_all_face_embeddings() -> List[FaceData]:
    """
    Get all face embeddings with their metadata.

    Returns:
        List of dictionaries containing: image_path, face_id, embeddings, confidence, bbox, cluster_id
    """
    from app.utils.path_id_mapping import get_path_from_id

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT face_id, image_id, embeddings, confidence, bbox, cluster_id FROM faces
    """
    )

    results = cursor.fetchall()
    conn.close()

    all_faces = []
    for face_id, image_id, embeddings_blob, confidence, bbox_json, cluster_id in results:
        image_path = get_path_from_id(image_id)

        # Convert BLOB back to numpy array
        embeddings = np.frombuffer(embeddings_blob, dtype=np.float64)

        # Parse bbox JSON if present
        bbox = json.loads(bbox_json) if bbox_json else None

        all_faces.append(
            {
                "face_id": face_id,
                "image_path": image_path,
                "image_id": image_id,
                "embeddings": embeddings,
                "confidence": confidence,
                "bbox": bbox,
                "cluster_id": cluster_id,
            }
        )

    return all_faces


def db_delete_face_embeddings_by_image_id(image_id: ImageId) -> None:
    """Delete all face embeddings for a specific image."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))

    conn.commit()
    conn.close()


def db_delete_face_embedding_by_face_id(face_id: FaceId) -> None:
    """Delete a specific face embedding by face_id."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM faces WHERE face_id = ?", (face_id,))

    conn.commit()
    conn.close()


def db_update_face_cluster_id(face_id: FaceId, cluster_id: Optional[ClusterId]) -> None:
    """Update the cluster_id for a specific face."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE faces SET cluster_id = ? WHERE face_id = ?", (cluster_id, face_id))

    conn.commit()
    conn.close()


def db_update_face_cluster_ids_batch(face_cluster_mapping: FaceClusterMapping) -> None:
    """
    Update cluster_ids for multiple faces in a batch.

    Args:
        face_cluster_mapping: Dictionary mapping face_id to cluster_id
    """
    if not face_cluster_mapping:
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        for face_id, cluster_id in face_cluster_mapping.items():
            cursor.execute("UPDATE faces SET cluster_id = ? WHERE face_id = ?", (cluster_id, face_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def db_get_faces_by_cluster_id(cluster_id: ClusterId) -> List[FaceData]:
    """Get all faces belonging to a specific cluster."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT face_id, image_id, embeddings, confidence, bbox FROM faces
        WHERE cluster_id = ?
    """,
        (cluster_id,),
    )

    results = cursor.fetchall()
    conn.close()

    faces = []
    for face_id, image_id, embeddings_blob, confidence, bbox_json in results:
        # Convert BLOB back to numpy array
        embeddings = np.frombuffer(embeddings_blob, dtype=np.float64)

        # Parse bbox JSON if present
        bbox = json.loads(bbox_json) if bbox_json else None

        faces.append(
            {
                "face_id": face_id,
                "image_id": image_id,
                "embeddings": embeddings,
                "confidence": confidence,
                "bbox": bbox,
                "cluster_id": cluster_id,
            }
        )

    return faces


def db_cleanup_face_embeddings() -> int:
    """Remove face embeddings for images that no longer exist in the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT image_id FROM faces")
    face_image_ids = set(row[0] for row in cursor.fetchall())

    cursor.execute("SELECT id FROM images")
    valid_image_ids = set(row[0] for row in cursor.fetchall())

    orphaned_ids = face_image_ids - valid_image_ids

    for orphaned_id in orphaned_ids:
        cursor.execute("DELETE FROM faces WHERE image_id = ?", (orphaned_id,))

    conn.commit()
    conn.close()

    return len(orphaned_ids)
