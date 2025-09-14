# Standard library imports
import sqlite3
import json
import os
import datetime
from PIL import Image, ExifTags
from typing import List, Tuple, TypedDict

# App-specific imports
from app.config.settings import (
    DATABASE_PATH,
)

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
    metadata: dict
    isTagged: bool


ImageClassPair = Tuple[ImageId, ClassId]


def extract_image_metadata(image_path: str) -> dict:
    """Extract metadata for a given image file with detailed debug logging."""
    # print(f"[DEBUG] extract_image_metadata called for: {image_path}")

    if not os.path.exists(image_path):
        return {
            "name": os.path.basename(image_path),
            "date_created": None,
            "width": 0,
            "height": 0,
            "file_location": image_path,
            "file_size": 0,
            "item_type": "unknown",
        }

    try:
        stats = os.stat(image_path)
        # print(f"[DEBUG] File exists. Size = {stats.st_size} bytes")

        try:
            with Image.open(image_path) as img:
                width, height = img.size
                mime_type = Image.MIME.get(img.format, "unknown")
                # print(f"[DEBUG] Pillow opened image: {width}x{height}, type={mime_type}")

                exif = getattr(img, "_getexif", lambda: None)() or {}
                dt_original = None
                for k, v in exif.items() if isinstance(exif, dict) else []:
                    if ExifTags.TAGS.get(k) == "DateTimeOriginal":
                        dt_original = v
                        break
            return {
                "name": os.path.basename(image_path),
                "date_created": (
                    datetime.datetime.strptime(
                        dt_original, "%Y:%m:%d %H:%M:%S"
                    ).isoformat()
                    if dt_original
                    else datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                ),
                "width": width,
                "height": height,
                "file_location": image_path,
                "file_size": stats.st_size,
                "item_type": mime_type,
            }

        except Exception:
            # print(f"[ERROR] Pillow could not open image {image_path} -> {e}")
            return {
                "name": os.path.basename(image_path),
                "date_created": datetime.datetime.fromtimestamp(
                    stats.st_mtime
                ).isoformat(),
                "file_location": image_path,
                "file_size": stats.st_size,
                "width": 0,
                "height": 0,
                "item_type": "unknown",
            }

    except Exception:
        return {
            "name": os.path.basename(image_path),
            "date_created": None,
            "width": 0,
            "height": 0,
            "file_location": image_path,
            "file_size": 0,
            "item_type": "unknown",
        }


def db_create_images_table() -> None:
    conn = sqlite3.connect(DATABASE_PATH)
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

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Ensure metadata is properly filled and JSON stringified
        prepared_records = []
        for record in image_records:
            metadata = record.get("metadata")

            # Normalize: if metadata is a string, try to parse it
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except Exception:
                    metadata = {}

            # print(f"[DEBUG] Incoming metadata for {record['path']}: {metadata} (type={type(metadata)})")

            # If no metadata provided or it's empty, extract it
            if not metadata or metadata == {}:
                metadata = extract_image_metadata(record["path"])

            # Make sure it's stored as a JSON string in DB
            record["metadata"] = json.dumps(metadata)

            prepared_records.append(record)

        # print("Prepared metadata:", prepared_records[0]["metadata"])

        cursor.executemany(
            """
            INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged)
            ON CONFLICT(id) DO UPDATE SET
              path=excluded.path,
              folder_id=excluded.folder_id,
              thumbnailPath=excluded.thumbnailPath,
              metadata=excluded.metadata,
              isTagged=excluded.isTagged
            """,
            prepared_records,
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting image records: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_images() -> List[dict]:
    """
    Get all images from the database with their tags.

    Returns:
        List of dictionaries containing all image data including tags
    """
    conn = sqlite3.connect(DATABASE_PATH)
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
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            ORDER BY i.path, m.name
            """
        )

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
            tag_name,
        ) in results:
            if image_id not in images_dict:
                # Safely parse metadata JSON -> dict
                metadata_dict = {}
                if metadata:
                    try:
                        parsed = (
                            json.loads(metadata)
                            if isinstance(metadata, str)
                            else metadata
                        )
                        metadata_dict = parsed if isinstance(parsed, dict) else {}
                    except (json.JSONDecodeError, TypeError, ValueError):
                        metadata_dict = {}

                images_dict[image_id] = {
                    "id": image_id,
                    "path": path,
                    "folder_id": folder_id,
                    "thumbnailPath": thumbnail_path,
                    "metadata": metadata_dict,
                    "isTagged": bool(is_tagged),
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
        print(f"Error getting all images: {e}")
        return []
    finally:
        conn.close()


def db_get_untagged_images() -> List[ImageRecord]:
    """
    Find all images that need AI tagging.
    Returns images where:
    - The image's folder has AI_Tagging enabled (True)
    - The image has isTagged set to False

    Returns:
        List of dictionaries containing image data: id, path, folder_id, thumbnailPath, metadata
    """
    conn = sqlite3.connect(DATABASE_PATH)
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
            md: dict = {}
            if metadata:
                try:
                    md = (
                        json.loads(metadata)
                        if isinstance(metadata, str)
                        else (metadata or {})
                    )
                except Exception:
                    md = {}
            untagged_images.append(
                {
                    "id": image_id,
                    "path": path,
                    "folder_id": folder_id,
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE images SET isTagged = ? WHERE id = ?",
            (is_tagged, image_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating image tagged status: {e}")
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

    conn = sqlite3.connect(DATABASE_PATH)
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
        print(f"Error inserting image classes: {e}")
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

    conn = sqlite3.connect(DATABASE_PATH)
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
        print(f"Error getting images by folder IDs: {e}")
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

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Create placeholders for the IN clause
        placeholders = ",".join("?" for _ in image_ids)
        cursor.execute(
            f"DELETE FROM images WHERE id IN ({placeholders})",
            image_ids,
        )
        conn.commit()
        print(f"Deleted {cursor.rowcount} obsolete image(s) from database")
        return True
    except Exception as e:
        print(f"Error deleting images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
