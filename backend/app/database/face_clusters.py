import sqlite3
from typing import Optional, List, Dict, TypedDict, Union
from app.config.settings import DATABASE_PATH

# Type definitions
ClusterId = str
ClusterName = str


class ClusterData(TypedDict):
    """Represents the full clusters table structure"""

    cluster_id: ClusterId
    cluster_name: Optional[ClusterName]
    face_image_base64: Optional[str]


ClusterMap = Dict[ClusterId, ClusterData]


def db_create_clusters_table() -> None:
    """Create the face_clusters table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS face_clusters (
            cluster_id TEXT PRIMARY KEY,
            cluster_name TEXT,
            face_image_base64 TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def db_insert_clusters_batch(clusters: List[ClusterData]) -> List[ClusterId]:
    """
    Insert multiple clusters into the database in batch.

    Args:
        clusters: List of ClusterData objects containing cluster information.
        cluster_id: should be provided as UUID strings.

    Returns:
        List of cluster IDs of the newly created clusters
    """
    if not clusters:
        return []

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cluster_ids = []
        insert_data = []

        for cluster in clusters:
            cluster_id = cluster.get("cluster_id")
            cluster_name = cluster.get("cluster_name")
            face_image_base64 = cluster.get("face_image_base64")

            insert_data.append((cluster_id, cluster_name, face_image_base64))
            cluster_ids.append(cluster_id)

        cursor.executemany(
            """
            INSERT INTO face_clusters (cluster_id, cluster_name, face_image_base64)
            VALUES (?, ?, ?)
        """,
            insert_data,
        )

        conn.commit()
        return cluster_ids
    finally:
        conn.close()


def db_get_cluster_by_id(cluster_id: ClusterId) -> Optional[ClusterData]:
    """
    Retrieve a cluster by its ID.

    Args:
        cluster_id: The ID of the cluster to retrieve

    Returns:
        ClusterData if found, None otherwise
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT cluster_id, cluster_name, face_image_base64 FROM face_clusters WHERE cluster_id = ?",
            (cluster_id,),
        )

        row = cursor.fetchone()

        if row:
            return ClusterData(
                cluster_id=row[0], cluster_name=row[1], face_image_base64=row[2]
            )
        return None
    finally:
        conn.close()


def db_get_all_clusters() -> List[ClusterData]:
    """
    Retrieve all clusters from the database.

    Returns:
        List of ClusterData objects
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT cluster_id, cluster_name, face_image_base64 FROM face_clusters ORDER BY cluster_id"
        )

        rows = cursor.fetchall()

        clusters = []
        for row in rows:
            clusters.append(
                ClusterData(
                    cluster_id=row[0], cluster_name=row[1], face_image_base64=row[2]
                )
            )

        return clusters
    finally:
        conn.close()


def db_update_cluster(
    cluster_id: ClusterId,
    cluster_name: Optional[ClusterName] = None,
) -> bool:
    """
    Update an existing cluster.

    Args:
        cluster_id: The ID of the cluster to update
        cluster_name: New cluster name (optional)

    Returns:
        True if the cluster was updated, False if not found
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Build the update query dynamically based on provided parameters
        update_fields = []
        update_values = []

        if cluster_name is not None:
            update_fields.append("cluster_name = ?")
            update_values.append(cluster_name)

        if not update_fields:
            return False

        update_values.append(cluster_id)

        cursor.execute(
            f"UPDATE face_clusters SET {', '.join(update_fields)} WHERE cluster_id = ?",
            update_values,
        )

        updated = cursor.rowcount > 0
        conn.commit()
        return updated
    finally:
        conn.close()


def db_delete_all_clusters() -> int:
    """
    Delete all entries from the face_clusters table.

    Returns:
        Number of clusters deleted
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM face_clusters")

        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
    finally:
        conn.close()


def db_get_all_clusters_with_face_counts() -> (
    List[Dict[str, Union[str, Optional[str], int]]]
):
    """
    Retrieve all clusters with their face counts and stored face images.

    Returns:
        List of dictionaries containing cluster_id, cluster_name, face_count, and face_image_base64
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                fc.cluster_id, 
                fc.cluster_name, 
                COUNT(f.face_id) as face_count,
                fc.face_image_base64
            FROM face_clusters fc
            LEFT JOIN faces f ON fc.cluster_id = f.cluster_id
            GROUP BY fc.cluster_id, fc.cluster_name, fc.face_image_base64
            ORDER BY fc.cluster_id
            """
        )

        rows = cursor.fetchall()

        clusters = []
        for row in rows:
            cluster_id, cluster_name, face_count, face_image_base64 = row
            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "face_count": face_count,
                    "face_image_base64": face_image_base64,
                }
            )

        return clusters
    finally:
        conn.close()


def db_get_images_by_cluster_id(
    cluster_id: ClusterId,
) -> List[Dict[str, Union[str, int]]]:
    """
    Get all images that contain faces belonging to a specific cluster.

    Args:
        cluster_id: The ID of the cluster to get images for

    Returns:
        List of dictionaries containing image data with face information
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT DISTINCT 
                i.id as image_id,
                i.path as image_path,
                i.thumbnailPath as thumbnail_path,
                i.metadata,
                f.face_id,
                f.confidence,
                f.bbox
            FROM images i
            INNER JOIN faces f ON i.id = f.image_id
            WHERE f.cluster_id = ?
            ORDER BY i.path
            """,
            (cluster_id,),
        )

        rows = cursor.fetchall()

        images = []
        for row in rows:
            (
                image_id,
                image_path,
                thumbnail_path,
                metadata,
                face_id,
                confidence,
                bbox_json,
            ) = row

            # Parse bbox JSON if it exists
            bbox = None
            if bbox_json:
                import json

                bbox = json.loads(bbox_json)

            images.append(
                {
                    "image_id": image_id,
                    "image_path": image_path,
                    "thumbnail_path": thumbnail_path,
                    "metadata": metadata,
                    "face_id": face_id,
                    "confidence": confidence,
                    "bbox": bbox,
                }
            )

        return images
    finally:
        conn.close()
