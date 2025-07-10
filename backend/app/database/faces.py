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
FaceEmbedding = str


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
            embeddings TEXT,
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

    embeddings_json = json.dumps([emb.tolist() for emb in embeddings])

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
    conn.close()
    return face_id


def db_insert_face_embeddings_by_image_id(
    image_id: ImageId,
    embeddings: Union[FaceEmbedding, List[FaceEmbedding]],
    confidence: Optional[Union[float, List[float]]] = None,
    bbox: Optional[Union[BoundingBox, List[BoundingBox]]] = None,
    cluster_id: Optional[Union[ClusterId, List[ClusterId]]] = None,
) -> Union[FaceId, List[FaceId]]:
    """
    Insert face embeddings using image path (convenience function).

    Args:
        image_id: Image ID (uuid string)
        embeddings: Face embedding vector (numpy array) or list of embeddings
        confidence: Confidence score(s) for face detection (optional)
        bbox: Bounding box coordinates or list of bounding boxes (optional)
        cluster_id: Cluster ID(s) for the face(s) (optional)
    """

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
