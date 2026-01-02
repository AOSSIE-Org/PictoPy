# Standard library imports
import sqlite3
from typing import Any, List, Mapping, Tuple, TypedDict, Union, Optional
from datetime import datetime, timedelta

# App-specific imports
from app.config.settings import (
    DATABASE_PATH,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Type definitions
ImageId = str
ImagePath = str
FolderId = str
ClassId = int


class ImageRecord(TypedDict):
    """Represents the full images table structure"""

    id: ImageId
    path: ImagePath
    folder_id: FolderId
    thumbnailPath: str
    metadata: Union[Mapping[str, Any], str]
    isTagged: bool
    is_deleted: bool
    deleted_at: Optional[str]


class UntaggedImageRecord(TypedDict):
    """Represents an image record returned for tagging."""

    id: ImageId
    path: ImagePath
    folder_id: FolderId
    thumbnailPath: str
    metadata: Mapping[str, Any]


ImageClassPair = Tuple[ImageId, ClassId]


class ActionHistoryRecord(TypedDict):
    """Represents an action history record"""

    id: int
    action_type: str
    entity_type: str
    entity_id: str
    timestamp: str
    metadata: Optional[str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    # Ensure ON DELETE CASCADE and other FKs are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_images_table() -> None:
    conn = _connect()
    cursor = conn.cursor()

    # Create new images table with merged fields
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            path VARCHAR UNIQUE,
            folder_id INTEGER,
            thumbnailPath TEXT UNIQUE,
            metadata TEXT,
            isTagged BOOLEAN DEFAULT 0,
            isFavourite BOOLEAN DEFAULT 0,
            is_deleted BOOLEAN DEFAULT 0,
            deleted_at DATETIME,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    # Create new image_classes junction table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS image_classes (
            image_id TEXT,
            class_id INTEGER,
            PRIMARY KEY (image_id, class_id),
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
            FOREIGN KEY (class_id) REFERENCES mappings(class_id) ON DELETE CASCADE
        )
    """
    )

    # Create action_history table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """
    )

    # Create indexes
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_action_history_timestamp
        ON action_history(timestamp DESC)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_images_is_deleted
        ON images(is_deleted)
    """
    )

    conn.commit()
    conn.close()


def db_bulk_insert_images(image_records: List[ImageRecord]) -> bool:
    """Insert multiple image records in a single transaction."""
    if not image_records:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """
            INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged, is_deleted, deleted_at)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged, 0, NULL)
            ON CONFLICT(path) DO UPDATE SET
                folder_id=excluded.folder_id,
                thumbnailPath=excluded.thumbnailPath,
                metadata=excluded.metadata,
                isTagged=CASE
                    WHEN excluded.isTagged THEN 1
                    ELSE images.isTagged
                END
            """,
            image_records,
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting image records: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_images(
    tagged: Union[bool, None] = None, include_deleted: bool = False
) -> List[dict]:
    """
    Get all images from the database with their tags.

    Args:
        tagged: Optional filter for tagged status. If None, returns all images.
                If True, returns only tagged images. If False, returns only untagged images.

    Returns:
        List of dictionaries containing all image data including tags
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        # Build the query with optional WHERE clause
        query = """
            SELECT 
                i.id, 
                i.path, 
                i.folder_id, 
                i.thumbnailPath, 
                i.metadata, 
                i.isTagged,
                i.isFavourite,
                i.is_deleted,
                i.deleted_at,
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
        """

        params = []
        where_conditions = []

        if tagged is not None:
            where_conditions.append("i.isTagged = ?")
            params.append(tagged)

        if not include_deleted:
            where_conditions.append("i.is_deleted = 0")

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        query += " ORDER BY i.path, m.name"

        cursor.execute(query, params)

        results = cursor.fetchall()

        # Group results by image ID
        images_dict = {}
        for (
            image_id,
            path,
            folder_id,
            thumbnail_path,
            metadata,
            is_tagged,
            is_favourite,
            is_deleted,
            deleted_at,
            tag_name,
        ) in results:
            if image_id not in images_dict:
                # Safely parse metadata JSON -> dict
                from app.utils.images import image_util_parse_metadata

                metadata_dict = image_util_parse_metadata(metadata)

                images_dict[image_id] = {
                    "id": image_id,
                    "path": path,
                    "folder_id": str(folder_id),
                    "thumbnailPath": thumbnail_path,
                    "metadata": metadata_dict,
                    "isTagged": bool(is_tagged),
                    "isFavourite": bool(is_favourite),
                    "is_deleted": bool(is_deleted),
                    "deleted_at": deleted_at,
                    "tags": [],
                }

            # Add tag if it exists (avoid duplicates)
            if tag_name and tag_name not in images_dict[image_id]["tags"]:
                images_dict[image_id]["tags"].append(tag_name)

        # Convert to list and set tags to None if empty
        images = []
        for image_data in images_dict.values():
            if not image_data["tags"]:
                image_data["tags"] = None
            images.append(image_data)

        # Sort by path
        images.sort(key=lambda x: x["path"])

        return images

    except Exception as e:
        logger.error(f"Error getting all images: {e}")
        return []
    finally:
        conn.close()


def db_get_untagged_images() -> List[UntaggedImageRecord]:
    """
    Find all images that need AI tagging.
    Returns images where:
    - The image's folder has AI_Tagging enabled (True)
    - The image has isTagged set to False

    Returns:
        List of dictionaries containing image data: id, path, folder_id, thumbnailPath, metadata
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT i.id, i.path, i.folder_id, i.thumbnailPath, i.metadata
            FROM images i
            JOIN folders f ON i.folder_id = f.folder_id
            WHERE f.AI_Tagging = TRUE
            AND i.isTagged = FALSE
            """
        )

        results = cursor.fetchall()

        untagged_images = []
        for image_id, path, folder_id, thumbnail_path, metadata in results:
            from app.utils.images import image_util_parse_metadata

            md = image_util_parse_metadata(metadata)
            untagged_images.append(
                {
                    "id": image_id,
                    "path": path,
                    "folder_id": str(folder_id) if folder_id is not None else None,
                    "thumbnailPath": thumbnail_path,
                    "metadata": md,
                }
            )

        return untagged_images

    finally:
        conn.close()


def db_update_image_tagged_status(image_id: ImageId, is_tagged: bool = True) -> bool:
    """
    Update the isTagged status for a specific image.

    Args:
        image_id: ID of the image to update
        is_tagged: Boolean value to set for isTagged (default True)

    Returns:
        True if update was successful, False otherwise
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE images SET isTagged = ? WHERE id = ?",
            (is_tagged, image_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating image tagged status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_insert_image_classes_batch(image_class_pairs: List[ImageClassPair]) -> bool:
    """
    Insert multiple image-class pairs into the image_classes table.

    Args:
        image_class_pairs: List of tuples containing (image_id, class_id) pairs

    Returns:
        True if insertion was successful, False otherwise
    """
    if not image_class_pairs:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO image_classes (image_id, class_id)
            VALUES (?, ?)
            """,
            image_class_pairs,
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting image classes: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_images_by_folder_ids(
    folder_ids: List[int],
) -> List[Tuple[ImageId, ImagePath, str]]:
    """
    Get all images that belong to the specified folder IDs.

    Args:
        folder_ids: List of folder IDs to search for images

    Returns:
        List of tuples containing (image_id, image_path, thumbnail_path)
    """
    if not folder_ids:
        return []

    conn = _connect()
    cursor = conn.cursor()

    try:
        # Create placeholders for the IN clause
        placeholders = ",".join("?" for _ in folder_ids)
        cursor.execute(
            f"""
            SELECT id, path, thumbnailPath
            FROM images
            WHERE folder_id IN ({placeholders})
            """,
            folder_ids,
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting images by folder IDs: {e}")
        return []
    finally:
        conn.close()


def db_delete_images_by_ids(image_ids: List[ImageId]) -> bool:
    """
    Delete multiple images from the database by their IDs.
    This will also delete associated records in image_classes due to CASCADE.

    Args:
        image_ids: List of image IDs to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    if not image_ids:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        # Create placeholders for the IN clause
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"DELETE FROM images WHERE id IN ({placeholders})",
            image_ids,
        )
        conn.commit()
        logger.info(f"Deleted {cursor.rowcount} obsolete image(s) from database")
        return True
    except Exception as e:
        logger.error(f"Error deleting images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_toggle_image_favourite_status(image_id: str) -> bool:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM images WHERE id = ?", (image_id,))
        if not cursor.fetchone():
            return False
        cursor.execute(
            """
            UPDATE images
            SET isFavourite = CASE WHEN isFavourite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (image_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_soft_delete_images(image_ids: List[ImageId]) -> bool:
    """
    Soft delete multiple images by setting is_deleted = 1 and deleted_at timestamp.

    Args:
        image_ids: List of image IDs to soft delete

    Returns:
        True if deletion was successful, False otherwise
    """
    if not image_ids:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        # Update images to be soft deleted
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"UPDATE images SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            image_ids,
        )

        # Remove from albums
        cursor.execute(
            f"DELETE FROM album_images WHERE image_id IN ({placeholders})",
            image_ids,
        )

        # Log the actions in history
        for image_id in image_ids:
            cursor.execute(
                """
                INSERT INTO action_history (action_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, ?)
                """,
                ("delete", "image", image_id, None),
            )
            cursor.execute(
                """
                INSERT INTO action_history (action_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "album_remove",
                    "album_image",
                    image_id,
                    '{"reason": "image_deleted"}',
                ),
            )

        conn.commit()
        logger.info(f"Soft deleted {cursor.rowcount} image(s)")
        return True
    except Exception as e:
        logger.error(f"Error soft deleting images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_restore_images(image_ids: List[ImageId]) -> bool:
    """
    Restore multiple soft deleted images.

    Args:
        image_ids: List of image IDs to restore

    Returns:
        True if restoration was successful, False otherwise
    """
    if not image_ids:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        # Update images to be restored
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"UPDATE images SET is_deleted = 0, deleted_at = NULL WHERE id IN ({placeholders})",
            image_ids,
        )

        # Log the action in history
        for image_id in image_ids:
            cursor.execute(
                """
                INSERT INTO action_history (action_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, ?)
                """,
                ("restore", "image", image_id, None),
            )

        conn.commit()
        logger.info(f"Restored {cursor.rowcount} image(s)")
        return True
    except Exception as e:
        logger.error(f"Error restoring images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_deleted_images() -> List[dict]:
    """
    Get all soft deleted images.

    Returns:
        List of deleted image dictionaries
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, isTagged, isFavourite, deleted_at
            FROM images
            WHERE is_deleted = 1
            ORDER BY deleted_at DESC
            """
        )

        results = cursor.fetchall()
        deleted_images = []

        for (
            image_id,
            path,
            folder_id,
            thumbnail_path,
            metadata,
            is_tagged,
            is_favourite,
            deleted_at,
        ) in results:
            from app.utils.images import image_util_parse_metadata

            metadata_dict = image_util_parse_metadata(metadata)

            deleted_images.append(
                {
                    "id": image_id,
                    "path": path,
                    "folder_id": str(folder_id),
                    "thumbnailPath": thumbnail_path,
                    "metadata": metadata_dict,
                    "isTagged": bool(is_tagged),
                    "isFavourite": bool(is_favourite),
                    "deleted_at": deleted_at,
                }
            )

        return deleted_images

    except Exception as e:
        logger.error(f"Error getting deleted images: {e}")
        return []
    finally:
        conn.close()


def db_permanently_delete_old_images(days: int = 30) -> int:
    """
    Permanently delete images that have been soft deleted for more than the specified days.

    Args:
        days: Number of days after which to permanently delete

    Returns:
        Number of images permanently deleted
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        # Calculate the cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get IDs of images to permanently delete
        cursor.execute(
            "SELECT id FROM images WHERE is_deleted = 1 AND deleted_at < ?",
            (cutoff_date,),
        )

        image_ids = [row[0] for row in cursor.fetchall()]

        if not image_ids:
            return 0

        # Permanently delete the images (this will cascade to image_classes)
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"DELETE FROM images WHERE id IN ({placeholders})",
            image_ids,
        )

        deleted_count = cursor.rowcount

        # Log the permanent deletion
        for image_id in image_ids:
            cursor.execute(
                """
                INSERT INTO action_history (action_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, ?)
                """,
                ("permanent_delete", "image", image_id, f'{{"days": {days}}}'),
            )

        conn.commit()
        logger.info(f"Permanently deleted {deleted_count} old image(s)")
        return deleted_count

    except Exception as e:
        logger.error(f"Error permanently deleting old images: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def db_permanently_delete_images(image_ids: List[ImageId]) -> bool:
    """
    Permanently delete specific images from history.

    Args:
        image_ids: List of image IDs to permanently delete

    Returns:
        True if deletion was successful, False otherwise
    """
    if not image_ids:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        # Permanently delete the images (this will cascade to image_classes)
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"DELETE FROM images WHERE id IN ({placeholders})",
            image_ids,
        )

        # Log the permanent deletion
        for image_id in image_ids:
            cursor.execute(
                """
                INSERT INTO action_history (action_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, ?)
                """,
                ("manual_permanent_delete", "image", image_id, None),
            )

        conn.commit()
        logger.info(f"Manually permanently deleted {cursor.rowcount} image(s)")
        return True
    except Exception as e:
        logger.error(f"Error permanently deleting images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
