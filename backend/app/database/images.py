# Standard library imports
import sqlite3
from typing import Any, List, Mapping, Tuple, TypedDict, Union

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


class UntaggedImageRecord(TypedDict):
    """Represents an image record returned for tagging."""

    id: ImageId
    path: ImagePath
    folder_id: FolderId
    thumbnailPath: str
    metadata: Mapping[str, Any]


ImageClassPair = Tuple[ImageId, ClassId]


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
            INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged)
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


def db_get_all_images(tagged: Union[bool, None] = None) -> List[dict]:
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
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
        """

        params = []
        if tagged is not None:
            query += " WHERE i.isTagged = ?"
            params.append(tagged)

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


def db_toggle_image_favourite_status(image_id: str) -> Union[bool, None]:
    """
    Toggle the favourite status of an image.
    
    Args:
        image_id: The ID of the image to toggle
        
    Returns:
        The new isFavourite status (True/False) if successful, None if image not found
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, isFavourite FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        current_status = bool(row[1])
        new_status = not current_status
        
        cursor.execute(
            "UPDATE images SET isFavourite = ? WHERE id = ?",
            (new_status, image_id),
        )
        conn.commit()
        return new_status if cursor.rowcount > 0 else None
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def db_get_image_by_id(image_id: str) -> Union[dict, None]:
    """
    Get a single image by its ID - O(1) lookup.
    
    Args:
        image_id: The ID of the image to retrieve
        
    Returns:
        Dictionary containing image data, or None if not found
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT 
                i.id, 
                i.path, 
                i.folder_id, 
                i.thumbnailPath, 
                i.metadata, 
                i.isTagged,
                i.isFavourite,
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.id = ?
            ORDER BY m.name
            """,
            (image_id,)
        )
        
        results = cursor.fetchall()
        
        if not results:
            return None
        
        # Process the first row for image data
        first_row = results[0]
        from app.utils.images import image_util_parse_metadata
        
        image_data = {
            "id": first_row[0],
            "path": first_row[1],
            "folder_id": str(first_row[2]),
            "thumbnailPath": first_row[3],
            "metadata": image_util_parse_metadata(first_row[4]),
            "isTagged": bool(first_row[5]),
            "isFavourite": bool(first_row[6]),
            "tags": [],
        }
        
        # Collect all tags
        for row in results:
            tag_name = row[7]
            if tag_name and tag_name not in image_data["tags"]:
                image_data["tags"].append(tag_name)
        
        if not image_data["tags"]:
            image_data["tags"] = None
            
        return image_data
        
    except Exception as e:
        logger.error(f"Error getting image by ID: {e}")
        return None
    finally:
        conn.close()
