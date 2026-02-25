"""
Database layer for manual cluster management.

Manual clusters are user-created groupings of images, independent from
AI-generated face clusters. They use a separate table to ensure no
interference with the AI auto-clustering logic.
"""

from datetime import datetime, timezone
from typing import List, Optional, TypedDict

from app.database.connection import get_db_connection


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

ClusterId = str
ImageId = str


class ManualClusterRecord(TypedDict):
    cluster_id: str
    name: str
    created_at: str
    updated_at: str
    is_auto_generated: bool


class ClusterImageRecord(TypedDict):
    id: int
    cluster_id: str
    image_id: str


# ---------------------------------------------------------------------------
# Table bootstrap (called once at startup)
# ---------------------------------------------------------------------------


def db_create_manual_clusters_table() -> None:
    """Create manual_clusters and manual_cluster_images tables if not exists."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_clusters (
                cluster_id   TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                is_auto_generated INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_cluster_images (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id TEXT NOT NULL,
                image_id   TEXT NOT NULL,
                UNIQUE (cluster_id, image_id),
                FOREIGN KEY (cluster_id) REFERENCES manual_clusters(cluster_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id)
                    ON DELETE CASCADE
            )
            """
        )


# ---------------------------------------------------------------------------
# Cluster CRUD
# ---------------------------------------------------------------------------


def db_insert_manual_cluster(
    cluster_id: str,
    name: str,
    is_auto_generated: bool = False,
) -> ManualClusterRecord:
    """Insert a new manual cluster row and return it."""
    now = _utcnow()
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO manual_clusters (cluster_id, name, created_at, updated_at, is_auto_generated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cluster_id, name, now, now, int(is_auto_generated)),
        )
    return ManualClusterRecord(
        cluster_id=cluster_id,
        name=name,
        created_at=now,
        updated_at=now,
        is_auto_generated=is_auto_generated,
    )


def db_get_all_manual_clusters() -> List[ManualClusterRecord]:
    """Return all manual clusters ordered by creation date descending."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                mc.cluster_id,
                mc.name,
                mc.created_at,
                mc.updated_at,
                mc.is_auto_generated,
                COUNT(mci.id) AS image_count
            FROM manual_clusters mc
            LEFT JOIN manual_cluster_images mci ON mc.cluster_id = mci.cluster_id
            GROUP BY mc.cluster_id
            ORDER BY mc.created_at DESC
            """
        )
        rows = cursor.fetchall()

    return [_row_to_cluster(row, include_count=True) for row in rows]


def db_get_manual_cluster_by_id(cluster_id: str) -> Optional[ManualClusterRecord]:
    """Fetch a single cluster by its primary key.  Returns None if not found."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                mc.cluster_id,
                mc.name,
                mc.created_at,
                mc.updated_at,
                mc.is_auto_generated,
                COUNT(mci.id) AS image_count
            FROM manual_clusters mc
            LEFT JOIN manual_cluster_images mci ON mc.cluster_id = mci.cluster_id
            WHERE mc.cluster_id = ?
            GROUP BY mc.cluster_id
            """,
            (cluster_id,),
        )
        row = cursor.fetchone()

    return _row_to_cluster(row, include_count=True) if row else None


def db_update_manual_cluster_name(cluster_id: str, name: str) -> bool:
    """Rename a cluster.  Returns True if a row was actually updated."""
    now = _utcnow()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "UPDATE manual_clusters SET name = ?, updated_at = ? WHERE cluster_id = ?",
            (name, now, cluster_id),
        )
        return cursor.rowcount > 0


def db_delete_manual_cluster(cluster_id: str) -> bool:
    """Delete a cluster (cascades to manual_cluster_images)."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM manual_clusters WHERE cluster_id = ?",
            (cluster_id,),
        )
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Image–cluster mapping
# ---------------------------------------------------------------------------


def db_get_images_in_manual_cluster(cluster_id: str) -> List[dict]:
    """
    Return image rows belonging to a cluster, joined with the images table.
    Each dict mirrors the Image type in the frontend.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                i.id,
                i.path,
                i.thumbnailPath,
                i.metadata
            FROM manual_cluster_images mci
            JOIN images i ON mci.image_id = i.id
            WHERE mci.cluster_id = ?
            ORDER BY mci.id ASC
            """,
            (cluster_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "path": row[1],
            "thumbnailPath": row[2],
            "metadata": row[3],
        }
        for row in rows
    ]


def db_add_images_to_manual_cluster(cluster_id: str, image_ids: List[str]) -> List[str]:
    """
    Bulk-assign image_ids to cluster_id.

    Skips already-assigned images (INSERT OR IGNORE).
    Returns the list of image_ids that were actually inserted (not already present).
    """
    inserted: List[str] = []
    with get_db_connection() as conn:
        for image_id in image_ids:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO manual_cluster_images (cluster_id, image_id)
                VALUES (?, ?)
                """,
                (cluster_id, image_id),
            )
            if cursor.rowcount > 0:
                inserted.append(image_id)
        # Bump updated_at on the parent cluster
        conn.execute(
            "UPDATE manual_clusters SET updated_at = ? WHERE cluster_id = ?",
            (_utcnow(), cluster_id),
        )
    return inserted


def db_remove_image_from_manual_cluster(cluster_id: str, image_id: str) -> bool:
    """Remove a single image from a cluster.  Returns True if removed."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM manual_cluster_images
            WHERE cluster_id = ? AND image_id = ?
            """,
            (cluster_id, image_id),
        )
        if cursor.rowcount > 0:
            conn.execute(
                "UPDATE manual_clusters SET updated_at = ? WHERE cluster_id = ?",
                (_utcnow(), cluster_id),
            )
    return cursor.rowcount > 0


def db_images_exist(image_ids: List[str]) -> List[str]:
    """
    Return the subset of image_ids that actually exist in the images table.
    Used to validate bulk assignment requests.
    """
    if not image_ids:
        return []
    placeholders = ",".join("?" * len(image_ids))
    with get_db_connection() as conn:
        cursor = conn.execute(
            f"SELECT id FROM images WHERE id IN ({placeholders})",
            image_ids,
        )
        return [row[0] for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_cluster(row: tuple, *, include_count: bool = False) -> dict:
    result = {
        "cluster_id": row[0],
        "name": row[1],
        "created_at": row[2],
        "updated_at": row[3],
        "is_auto_generated": bool(row[4]),
    }
    if include_count:
        result["image_count"] = row[5] if len(row) > 5 else 0
    return result
