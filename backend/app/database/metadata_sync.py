"""
Which photos still need their metadata written into the file, and what to write.

The database stays the fast index; the file is what survives PictoPy. These
queries pull together the pieces the packet is built from, none of which live
in one table.
"""

import json
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Tuple, TypedDict

from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

ImageId = str


class SyncCandidate(TypedDict):
    """Everything the packet for one photo is built from."""

    id: ImageId
    path: str
    metadata: Mapping[str, Any]
    is_favourite: bool
    keywords: List[str]
    faces: List[Dict[str, Any]]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _parse_json(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return fallback


def db_get_images_pending_metadata_sync(limit: int = 200) -> List[SyncCandidate]:
    """
    Photos whose file does not yet carry what the database knows.

    Only tagged photos are returned: writing before the AI pass has run would
    put an empty keyword list into the file and need a second write anyway.
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, metadata, isFavourite
            FROM images
            WHERE isMetadataSynced = 0 AND isTagged = 1
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        if not rows:
            return []

        candidates: Dict[ImageId, SyncCandidate] = {}
        for image_id, path, metadata, is_favourite in rows:
            candidates[image_id] = SyncCandidate(
                id=image_id,
                path=path,
                metadata=_parse_json(metadata, {}),
                is_favourite=bool(is_favourite),
                keywords=[],
                faces=[],
            )

        placeholders = ",".join("?" for _ in candidates)
        identifiers = list(candidates)

        # Tags come through the display view so the file gets the same labels
        # the gallery shows, rather than every low-scoring semantic match.
        cursor.execute(
            f"""
            SELECT d.image_id, m.name
            FROM image_classes_display d
            JOIN mappings m ON m.class_id = d.class_id
            WHERE d.image_id IN ({placeholders})
            ORDER BY m.name
            """,
            identifiers,
        )
        for image_id, name in cursor.fetchall():
            if name:
                candidates[image_id]["keywords"].append(name)

        # Only named clusters: an unnamed one carries no information a person
        # reading the file in another application could use.
        cursor.execute(
            f"""
            SELECT f.image_id, f.bbox, c.cluster_name
            FROM faces f
            JOIN face_clusters c ON c.cluster_id = f.cluster_id
            WHERE f.image_id IN ({placeholders})
              AND c.cluster_name IS NOT NULL
              AND TRIM(c.cluster_name) != ''
            ORDER BY c.cluster_name
            """,
            identifiers,
        )
        for image_id, bbox, cluster_name in cursor.fetchall():
            box = _parse_json(bbox, None)
            if isinstance(box, dict):
                candidates[image_id]["faces"].append(
                    {"name": cluster_name, "bbox": box}
                )

        return list(candidates.values())
    except sqlite3.Error as e:
        logger.error(f"Error collecting images pending metadata sync: {e}")
        return []
    finally:
        conn.close()


def db_count_images_pending_metadata_sync() -> int:
    """How many photos are waiting for their file to be brought up to date."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM images WHERE isMetadataSynced = 0 AND isTagged = 1"
        )
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        logger.error(f"Error counting images pending metadata sync: {e}")
        return 0
    finally:
        conn.close()


def db_mark_metadata_synced(written: List[Tuple[ImageId, int, int]]) -> int:
    """
    Record that a photo's file now carries its metadata, and how it now looks.

    The size and mtime go back into the metadata blob on purpose. Our own write
    changes both, and without this the next folder scan would see the file as
    user-modified, re-read it, and mark it for another write -- a loop the file
    itself keeps feeding.
    """
    if not written:
        return 0

    conn = _connect()
    cursor = conn.cursor()

    try:
        updated = 0
        for image_id, file_size, file_mtime in written:
            cursor.execute("SELECT metadata FROM images WHERE id = ?", (image_id,))
            row = cursor.fetchone()
            if row is None:
                continue

            metadata = _parse_json(row[0], {})
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["file_size"] = file_size
            metadata["file_mtime"] = file_mtime

            cursor.execute(
                """
                UPDATE images
                SET isMetadataSynced = 1, metadata = ?
                WHERE id = ?
                """,
                (json.dumps(metadata), image_id),
            )
            updated += cursor.rowcount

        conn.commit()
        return updated
    except sqlite3.Error as e:
        logger.error(f"Error marking metadata synced: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def db_mark_metadata_dirty(image_ids: List[ImageId]) -> int:
    """Flag photos whose file no longer matches what the database holds."""
    if not image_ids:
        return 0

    conn = _connect()
    cursor = conn.cursor()

    try:
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"UPDATE images SET isMetadataSynced = 0 WHERE id IN ({placeholders})",
            image_ids,
        )
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        logger.error(f"Error marking metadata dirty: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def db_mark_metadata_dirty_for_cluster(cluster_id: str) -> int:
    """
    Flag every photo showing a given person.

    Renaming a cluster changes one row but invalidates the region name written
    into every file that person appears in.
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE images SET isMetadataSynced = 0
            WHERE id IN (SELECT image_id FROM faces WHERE cluster_id = ?)
            """,
            (cluster_id,),
        )
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        logger.error(f"Error marking cluster {cluster_id} dirty: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()
