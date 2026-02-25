"""
Service layer for manual cluster management.

All business logic lives here; routes only call into this module and handle
HTTP-level concerns (status codes, serialization).
"""

from __future__ import annotations

import uuid
from typing import List

from app.database.manual_clusters import (
    db_add_images_to_manual_cluster,
    db_delete_manual_cluster,
    db_get_all_manual_clusters,
    db_get_images_in_manual_cluster,
    db_get_manual_cluster_by_id,
    db_images_exist,
    db_insert_manual_cluster,
    db_remove_image_from_manual_cluster,
    db_update_manual_cluster_name,
)
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions (translated to HTTP errors in the route layer)
# ---------------------------------------------------------------------------


class ClusterNotFoundError(Exception):
    pass


class ImageNotFoundError(Exception):
    def __init__(self, missing: List[str]):
        self.missing = missing
        super().__init__(f"Images not found: {missing}")


class DuplicateClusterNameError(Exception):
    pass


# ---------------------------------------------------------------------------
# Cluster CRUD
# ---------------------------------------------------------------------------


def create_cluster(name: str) -> dict:
    """
    Create a new manual cluster.

    Raises:
        DuplicateClusterNameError: placeholder – currently names are non-unique;
            extend here if you add a UNIQUE constraint on name.
    """
    cluster_id = str(uuid.uuid4())
    record = db_insert_manual_cluster(cluster_id, name, is_auto_generated=False)
    logger.info("Manual cluster created: id=%s name=%s", cluster_id, name)
    return record


def list_clusters() -> List[dict]:
    """Return all manual clusters with their image counts."""
    return db_get_all_manual_clusters()


def get_cluster(cluster_id: str) -> dict:
    """
    Return a cluster including its images.

    Raises:
        ClusterNotFoundError: if the cluster does not exist.
    """
    cluster = db_get_manual_cluster_by_id(cluster_id)
    if cluster is None:
        raise ClusterNotFoundError(cluster_id)

    images = db_get_images_in_manual_cluster(cluster_id)
    return {
        "cluster": cluster,
        "images": images,
        "image_count": len(images),
    }


def rename_cluster(cluster_id: str, name: str) -> dict:
    """
    Rename a cluster.

    Raises:
        ClusterNotFoundError: if the cluster does not exist.
    """
    # Raise early if cluster missing
    _require_cluster(cluster_id)
    db_update_manual_cluster_name(cluster_id, name)
    updated = db_get_manual_cluster_by_id(cluster_id)
    logger.info("Manual cluster renamed: id=%s new_name=%s", cluster_id, name)
    return updated  # type: ignore[return-value]


def delete_cluster(cluster_id: str) -> None:
    """
    Delete a cluster and all its image mappings.

    Raises:
        ClusterNotFoundError: if the cluster does not exist.
    """
    _require_cluster(cluster_id)
    db_delete_manual_cluster(cluster_id)
    logger.info("Manual cluster deleted: id=%s", cluster_id)


# ---------------------------------------------------------------------------
# Image assignment
# ---------------------------------------------------------------------------


def assign_images(cluster_id: str, image_ids: List[str]) -> dict:
    """
    Bulk-assign images to a cluster.

    - Validates that every image_id exists in the images table.
    - Skips already-assigned images (idempotent).

    Returns:
        dict with 'assigned_count' and 'skipped_count'.

    Raises:
        ClusterNotFoundError: cluster not found.
        ImageNotFoundError:   one or more image_ids do not exist.
    """
    _require_cluster(cluster_id)

    # Validate that all image_ids exist
    existing = set(db_images_exist(image_ids))
    missing = [iid for iid in image_ids if iid not in existing]
    if missing:
        raise ImageNotFoundError(missing)

    inserted = db_add_images_to_manual_cluster(cluster_id, image_ids)
    skipped = len(image_ids) - len(inserted)
    logger.info(
        "Assigned images to cluster %s: assigned=%d skipped=%d",
        cluster_id,
        len(inserted),
        skipped,
    )
    return {"assigned_count": len(inserted), "skipped_count": skipped}


def remove_image(cluster_id: str, image_id: str) -> None:
    """
    Remove a single image from a cluster.

    Raises:
        ClusterNotFoundError: cluster not found.
        ImageNotFoundError:   image is not assigned to this cluster.
    """
    _require_cluster(cluster_id)
    removed = db_remove_image_from_manual_cluster(cluster_id, image_id)
    if not removed:
        raise ImageNotFoundError([image_id])
    logger.info("Removed image %s from cluster %s", image_id, cluster_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_cluster(cluster_id: str) -> dict:
    """Raise ClusterNotFoundError if the cluster does not exist."""
    cluster = db_get_manual_cluster_by_id(cluster_id)
    if cluster is None:
        raise ClusterNotFoundError(cluster_id)
    return cluster
