import sqlite3
import json
import numpy as np
from typing import Optional, List, Dict, Union, TypedDict, Any
from app.config.settings import DATABASE_PATH

# Type definitions
FaceId = int
ImageId = str
ClusterId = str  # Consistent with TEXT in DB
FaceEmbedding = np.ndarray
BoundingBox = Dict[str, Union[int, float]]


class FaceData(TypedDict):
    """Represents the full faces table structure"""
    face_id: FaceId
    image_id: ImageId
    embeddings: FaceEmbedding
    confidence: Optional[float]
    bbox: Optional[BoundingBox]
    cluster_id: Optional[ClusterId]


def get_db_conn():
    """Helper to get connection with Foreign Keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_faces_table() -> None:
    """Create the faces table if it doesn't exist."""
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS faces (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT NOT NULL,
                cluster_id TEXT,
                embeddings JSON NOT NULL,
                confidence REAL,
                bbox JSON,
                FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE
            )
        """
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating faces table: {e}")
        raise
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
    """
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()

        embeddings_json = json.dumps(embeddings.tolist())
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
    except sqlite3.Error as e:
        print(f"Error inserting face embeddings: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn is not None:
            conn.close()


def db_insert_face_embeddings_by_image_id(
    image_id: ImageId,
    embeddings: Union[FaceEmbedding, List[FaceEmbedding]],
    confidence: Optional[Union[float, List[Optional[float]]]] = None,
    bbox: Optional[Union[BoundingBox, List[Optional[BoundingBox]]]] = None,
    cluster_id: Optional[Union[ClusterId, List[Optional[ClusterId]]]] = None,
) -> Union[Optional[FaceId], List[Optional[FaceId]]]:
    """
    Insert face embeddings with robust input handling.
    Safely handles single arrays, lists of arrays, and 2D numpy arrays.
    """
    
    # 1. Handle Empty List (Prevent Crash)
    if isinstance(embeddings, list) and len(embeddings) == 0:
        return []

    # 2. Handle 2D Numpy Array (Fixes CodeRabbit Issue)
    # If input is (N, 512), convert it to list of N arrays
    if isinstance(embeddings, np.ndarray) and embeddings.ndim == 2:
        embeddings = list(embeddings)

    # Check if we are handling a list of embeddings
    is_list_input = isinstance(embeddings, list) and len(embeddings) > 0 and isinstance(embeddings[0], np.ndarray)

    if is_list_input:
        face_ids: List[Optional[FaceId]] = []
        for i, emb in enumerate(embeddings):
            # Extract single confidence value safely
            conf: Optional[float] = None
            if isinstance(confidence, list) and i < len(confidence):
                conf = confidence[i]
            elif isinstance(confidence, (int, float)):
                conf = float(confidence)

            # Extract single bbox value safely
            bb: Optional[BoundingBox] = None
            if isinstance(bbox, list) and i < len(bbox):
                bb = bbox[i]
            elif isinstance(bbox, dict):
                bb = bbox

            # Extract single cluster_id value safely
            cid: Optional[ClusterId] = None
            if isinstance(cluster_id, list) and i < len(cluster_id):
                cid = cluster_id[i]
            elif isinstance(cluster_id, str):
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
        elif isinstance(cluster_id, str):
            single_cid = cluster_id

        return db_insert_face_embeddings(
            image_id, embeddings, single_conf, single_bbox, single_cid
        )


def get_all_face_embeddings() -> List[Dict[str, Any]]:
    """
    Get all face embeddings with associated image data.
    Filters out corrupted records where embeddings are missing.
    """
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()

        # Step 1: Get all faces with their image data
        # We explicitly select face_id to ensure uniqueness
        cursor.execute(
            """
            SELECT
                f.face_id,
                f.embeddings,
                f.bbox,
                i.id,
                i.path,
                i.folder_id,
                i.thumbnailPath,
                i.metadata,
                i.isTagged
            FROM faces f
            JOIN images i ON f.image_id = i.id
            ORDER BY i.path, f.face_id
            """
        )
        face_results = cursor.fetchall()

        # Step 2: Get tags for all images that have faces
        # We do this separately to avoid a Cartesian product in the main query
        cursor.execute(
            """
            SELECT DISTINCT i.id, m.name as tag_name
            FROM faces f
            JOIN images i ON f.image_id = i.id
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE m.name IS NOT NULL
            """
        )
        tag_results = cursor.fetchall()

        from app.utils.images import image_util_parse_metadata

        # Build a mapping of image_id -> list of tags
        image_tags: Dict[str, List[str]] = {}
        for image_id, tag_name in tag_results:
            if image_id not in image_tags:
                image_tags[image_id] = []
            if tag_name not in image_tags[image_id]:
                image_tags[image_id].append(tag_name)

        # Step 3: Construct the result list (one entry per face)
        faces: List[Dict[str, Any]] = []
        for (
            face_id,
            embeddings,
            bbox,
            image_id,
            path,
            folder_id,
            thumbnail_path,
            metadata,
            is_tagged,
        ) in face_results:
            try:
                # CRITICAL FIX: Handle Null/Empty embeddings to prevent downstream crashes
                if not embeddings:
                    continue
                    
                embeddings_json = json.loads(embeddings)
                bbox_json = json.loads(bbox) if bbox else None
                
                if embeddings_json is None:
                    continue

            except json.JSONDecodeError:
                print(f"Error decoding JSON for face {face_id}")
                continue

            # Attach tags belonging to this image
            tags = image_tags.get(image_id)
            if tags is not None and len(tags) == 0:
                tags = None

            faces.append({
                "face_id": face_id,
                "embeddings": embeddings_json,
                "bbox": bbox_json,
                # Image Metadata
                "id": image_id,
                "path": path,
                "folder_id": folder_id,
                "thumbnailPath": thumbnail_path,
                "metadata": image_util_parse_metadata(metadata),
                "isTagged": bool(is_tagged),
                "tags": tags,
            })

        return faces
    except sqlite3.Error as e:
        print(f"Error getting face embeddings: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_get_faces_unassigned_clusters() -> List[Dict[str, Union[FaceId, FaceEmbedding]]]:
    """Get faces that haven't been assigned to a cluster yet."""
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT face_id, embeddings FROM faces WHERE cluster_id IS NULL")
        rows = cursor.fetchall()

        faces: List[Dict[str, Union[FaceId, FaceEmbedding]]] = []
        for row in rows:
            face_id, embeddings_json = row
            if not embeddings_json:
                continue
            embeddings = np.array(json.loads(embeddings_json))
            faces.append({"face_id": face_id, "embeddings": embeddings})

        return faces
    except sqlite3.Error as e:
        print(f"Error getting unassigned faces: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_get_all_faces_with_cluster_names() -> List[Dict[str, Union[FaceId, FaceEmbedding, Optional[str]]]]:
    """Get all faces with their cluster names."""
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT f.face_id, f.embeddings, fc.cluster_name
            FROM faces f
            LEFT JOIN face_clusters fc ON f.cluster_id = fc.cluster_id
            """
        )
        rows = cursor.fetchall()

        faces: List[Dict[str, Union[FaceId, FaceEmbedding, Optional[str]]]] = []
        for row in rows:
            face_id, embeddings_json, cluster_name = row
            if not embeddings_json:
                continue
            embeddings = np.array(json.loads(embeddings_json))
            faces.append(
                {
                    "face_id": face_id,
                    "embeddings": embeddings,
                    "cluster_name": cluster_name,
                }
            )

        return faces
    except sqlite3.Error as e:
        print(f"Error getting faces with cluster names: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_update_face_cluster_ids_batch(
    face_cluster_mapping: List[Dict[str, Union[FaceId, ClusterId, None]]],
    cursor: Optional[sqlite3.Cursor] = None,
) -> None:
    """Update cluster IDs for multiple faces in batch."""
    if not face_cluster_mapping:
        return

    conn = None
    own_connection = cursor is None

    if own_connection:
        conn = get_db_conn()
        cursor = conn.cursor()

    # At this point cursor should never be None
    if cursor is None:
        raise ValueError("Database cursor is required")

    try:
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
    except sqlite3.Error as e:
        if own_connection and conn:
            conn.rollback()
        print(f"Error updating face cluster IDs in batch: {e}")
        raise
    finally:
        if own_connection and conn:
            conn.close()


def db_get_cluster_mean_embeddings() -> List[Dict[str, Union[int, FaceEmbedding]]]:
    """Get mean embeddings for each cluster."""
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT f.cluster_id, f.embeddings
            FROM faces f
            WHERE f.cluster_id IS NOT NULL
            """
        )
        rows = cursor.fetchall()

        if not rows:
            return []

        cluster_embeddings: Dict[str, List[np.ndarray]] = {}
        for row in rows:
            cluster_id, embeddings_json = row
            if not embeddings_json:
                continue
            embeddings = np.array(json.loads(embeddings_json))

            if cluster_id not in cluster_embeddings:
                cluster_embeddings[cluster_id] = []
            cluster_embeddings[cluster_id].append(embeddings)

        cluster_means: List[Dict[str, Union[int, FaceEmbedding]]] = []
        for cluster_id, embeddings_list in cluster_embeddings.items():
            # Stack all embeddings for this cluster and calculate mean
            stacked_embeddings = np.stack(embeddings_list)
            mean_embedding = np.mean(stacked_embeddings, axis=0)
            cluster_means.append(
                {"cluster_id": cluster_id, "mean_embedding": mean_embedding}
            )

        return cluster_means
    except sqlite3.Error as e:
        print(f"Error getting cluster mean embeddings: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()