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


ClusterMap = Dict[ClusterId, ClusterData]


def db_create_clusters_table() -> None:
    """Create the face_clusters table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS face_clusters (
            cluster_id TEXT PRIMARY KEY,
            cluster_name TEXT
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

    cluster_ids = []
    insert_data = []

    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        cluster_name = cluster.get("cluster_name")

        insert_data.append((cluster_id, cluster_name))
        cluster_ids.append(cluster_id)

    cursor.executemany(
        """
        INSERT INTO face_clusters (cluster_id, cluster_name)
        VALUES (?, ?)
    """,
        insert_data,
    )

    conn.commit()
    conn.close()

    return cluster_ids


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

    cursor.execute(
        "SELECT cluster_id, cluster_name FROM face_clusters WHERE cluster_id = ?",
        (cluster_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return ClusterData(cluster_id=row[0], cluster_name=row[1])
    return None


def db_get_all_clusters() -> List[ClusterData]:
    """
    Retrieve all clusters from the database.

    Returns:
        List of ClusterData objects
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT cluster_id, cluster_name FROM face_clusters ORDER BY cluster_id")

    rows = cursor.fetchall()
    conn.close()

    clusters = []
    for row in rows:
        clusters.append(ClusterData(cluster_id=row[0], cluster_name=row[1]))

    return clusters


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

    # Build the update query dynamically based on provided parameters
    update_fields = []
    update_values = []

    if cluster_name is not None:
        update_fields.append("cluster_name = ?")
        update_values.append(cluster_name)

    if not update_fields:
        conn.close()
        return False

    update_values.append(cluster_id)

    cursor.execute(f"UPDATE face_clusters SET {', '.join(update_fields)} WHERE cluster_id = ?", update_values)

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return updated


def db_delete_all_clusters() -> int:
    """
    Delete all entries from the face_clusters table.

    Returns:
        Number of clusters deleted
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM face_clusters")

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted_count


def db_get_all_clusters_with_face_counts() -> List[Dict[str, Union[str, Optional[str], int]]]:
    """
    Retrieve all clusters with their face counts.

    Returns:
        List of dictionaries containing cluster_id, cluster_name, and face_count
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT fc.cluster_id, fc.cluster_name, COUNT(f.face_id) as face_count
        FROM face_clusters fc
        LEFT JOIN faces f ON fc.cluster_id = f.cluster_id
        GROUP BY fc.cluster_id, fc.cluster_name
        ORDER BY fc.cluster_id
        """
    )

    rows = cursor.fetchall()
    conn.close()

    clusters = []
    for row in rows:
        clusters.append({"cluster_id": row[0], "cluster_name": row[1], "face_count": row[2]})

    return clusters
