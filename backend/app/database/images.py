# Standard library imports
import sqlite3
from typing import Any, Dict, List, Mapping, Tuple, TypedDict, Union, Optional
import json

from datetime import datetime

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


class ImageRecord(TypedDict, total=False):
    """Represents the full images table structure"""

    id: ImageId
    path: ImagePath
    folder_id: FolderId
    thumbnailPath: str
    metadata: Union[Mapping[str, Any], str]
    isTagged: bool
    isFavourite: bool
    isEmbedded: bool
    # New fields for Memories feature
    latitude: Optional[float]
    longitude: Optional[float]
    captured_at: Optional[datetime]


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

    # Create new images table with merged fields including Memories feature columns
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
            isEmbedded BOOLEAN DEFAULT 0,
            latitude REAL,
            longitude REAL,
            captured_at DATETIME,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    # Create indexes for Memories feature queries
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_latitude ON images(latitude)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_images_longitude ON images(longitude)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_images_captured_at ON images(captured_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_images_favourite_captured_at ON images(isFavourite, captured_at)"
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
            INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged, isEmbedded, latitude, longitude, captured_at)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged, COALESCE(:isEmbedded, 0), :latitude, :longitude, :captured_at)
            ON CONFLICT(path) DO UPDATE SET
                folder_id=excluded.folder_id,
                thumbnailPath=excluded.thumbnailPath,
                metadata=excluded.metadata,
                isTagged=CASE
                    WHEN excluded.isTagged THEN 1
                    ELSE images.isTagged
                END,
                isEmbedded=CASE
                    WHEN excluded.isEmbedded THEN 1
                    ELSE images.isEmbedded
                END,
                latitude=COALESCE(excluded.latitude, images.latitude),
                longitude=COALESCE(excluded.longitude, images.longitude),
                captured_at=COALESCE(excluded.captured_at, images.captured_at)
            """,
            image_records,
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
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
                i.latitude,
                i.longitude,
                i.captured_at,
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
            latitude,
            longitude,
            captured_at,
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
                    "latitude": latitude,
                    "longitude": longitude,
                    "captured_at": (
                        captured_at if captured_at else None
                    ),  # SQLite returns string
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

    except sqlite3.Error as e:
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


def db_get_unembedded_images() -> List[UntaggedImageRecord]:
    """
    Find all images that need SigLIP2 embedding.
    Returns images where:
    - The image's folder has AI_Tagging enabled (True)
    - The image has isEmbedded set to False

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
            AND i.isEmbedded = FALSE
            """
        )

        results = cursor.fetchall()

        unembedded_images = []
        for image_id, path, folder_id, thumbnail_path, metadata in results:
            from app.utils.images import image_util_parse_metadata

            md = image_util_parse_metadata(metadata)
            unembedded_images.append(
                {
                    "id": image_id,
                    "path": path,
                    "folder_id": str(folder_id) if folder_id is not None else None,
                    "thumbnailPath": thumbnail_path,
                    "metadata": md,
                }
            )

        return unembedded_images

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
    except sqlite3.Error as e:
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
    except sqlite3.Error as e:
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
    except sqlite3.Error as e:
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
    except sqlite3.Error as e:
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
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_image_by_id(image_id: str) -> Optional[dict]:
    """
    Get a single image by ID with its favorite status.
    """
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, isTagged, isFavourite
            FROM images
            WHERE id = ?
        """,
            (image_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        try:
            metadata = json.loads(row[4]) if row[4] else {}
        except json.JSONDecodeError:
            metadata = {}
        return {
            "id": row[0],
            "path": row[1],
            "folder_id": row[2],
            "thumbnailPath": row[3],
            "metadata": metadata,
            "isTagged": bool(row[5]),
            "isFavourite": bool(row[6]),
        }
    finally:
        conn.close()


def _group_image_rows_with_tags(
    rows: List[Tuple], images_dict: Dict[str, dict]
) -> None:
    """
    Group flat image+tag join rows (the shared 11-column SELECT shape used by
    db_search_images_by_tag and db_get_images_by_ids) into images_dict, keyed
    by image_id, aggregating tag_name into a deduplicated "tags" list.
    Mutates images_dict in place so callers can accumulate across chunks.
    """
    for (
        image_id,
        path,
        folder_id,
        thumbnail_path,
        metadata,
        is_tagged,
        is_favourite,
        latitude,
        longitude,
        captured_at,
        tag_name_result,
    ) in rows:
        if image_id not in images_dict:
            images_dict[image_id] = {
                "id": image_id,
                "path": path,
                "folder_id": str(folder_id) if folder_id is not None else "",
                "thumbnailPath": thumbnail_path,
                "metadata": metadata,
                "isTagged": bool(is_tagged),
                "isFavourite": bool(is_favourite),
                "latitude": latitude,
                "longitude": longitude,
                "captured_at": captured_at if captured_at else None,
                "tags": [],
            }

        if tag_name_result and tag_name_result not in images_dict[image_id]["tags"]:
            images_dict[image_id]["tags"].append(tag_name_result)


def _finalize_grouped_images(images_dict: Dict[str, dict]) -> List[dict]:
    """Convert an images_dict from _group_image_rows_with_tags into a list,
    normalizing an empty "tags" list to None."""
    images = []
    for image_data in images_dict.values():
        if not image_data["tags"]:
            image_data["tags"] = None
        images.append(image_data)
    return images


def db_search_images_by_tag(tag_name: str) -> List[dict]:
    """
    Get all images that match a specific tag name, returning their full tag list.
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                i.id,
                i.path,
                i.folder_id,
                i.thumbnailPath,
                i.metadata,
                i.isTagged,
                i.isFavourite,
                i.latitude,
                i.longitude,
                i.captured_at,
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.id IN (
                SELECT ic2.image_id FROM image_classes ic2
                JOIN mappings m2 ON ic2.class_id = m2.class_id
                WHERE LOWER(m2.name) = LOWER(?)
            )
            ORDER BY i.path, m.name
        """

        cursor.execute(query, [tag_name])
        results = cursor.fetchall()

        images_dict: Dict[str, dict] = {}
        _group_image_rows_with_tags(results, images_dict)
        images = _finalize_grouped_images(images_dict)

        images.sort(key=lambda x: x["path"])
        return images

    except sqlite3.Error as e:
        logger.error(f"Error searching images by tag: {e}")
        raise
    finally:
        conn.close()


def db_get_images_by_ids(image_ids: List[str]) -> List[dict]:
    """
    Get a list of images by their IDs, returning their full tag list.
    """
    if not image_ids:
        return []

    conn = _connect()
    cursor = conn.cursor()

    try:
        images_dict: Dict[str, dict] = {}
        chunk_size = 500

        for i in range(0, len(image_ids), chunk_size):
            chunk = image_ids[i : i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            query = f"""
                SELECT
                    i.id,
                    i.path,
                    i.folder_id,
                    i.thumbnailPath,
                    i.metadata,
                    i.isTagged,
                    i.isFavourite,
                    i.latitude,
                    i.longitude,
                    i.captured_at,
                    m.name as tag_name
                FROM images i
                LEFT JOIN image_classes ic ON i.id = ic.image_id
                LEFT JOIN mappings m ON ic.class_id = m.class_id
                WHERE i.id IN ({placeholders})
                ORDER BY i.path, m.name
            """

            cursor.execute(query, chunk)
            results = cursor.fetchall()
            _group_image_rows_with_tags(results, images_dict)

        images = _finalize_grouped_images(images_dict)

        # Preserve the original order from image_ids
        # Create a lookup for fast indexing
        image_lookup = {img["id"]: img for img in images}

        ordered_images = []
        for img_id in image_ids:
            if img_id in image_lookup:
                ordered_images.append(image_lookup[img_id])

        return ordered_images

    except sqlite3.Error as e:
        logger.error(f"Error getting images by IDs: {e}")
        raise
    finally:
        conn.close()


# ============================================================================
# MEMORIES FEATURE - Location and Time-based Queries
# ============================================================================


def db_get_images_by_date_range(
    start_date: datetime, end_date: datetime, include_favorites_only: bool = False
) -> List[dict]:
    """
    Get images captured within a date range for Memories timeline.

    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        include_favorites_only: If True, only return favorite images

    Returns:
        List of image dictionaries with location and time data
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        query = """
            SELECT 
                i.id, 
                i.path, 
                i.folder_id,
                i.thumbnailPath, 
                i.metadata,
                i.isTagged,
                i.isFavourite,
                i.latitude, 
                i.longitude, 
                i.captured_at,
                GROUP_CONCAT(m.name, ',') as tags
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.captured_at BETWEEN ? AND ?
        """

        params = [start_date, end_date]

        if include_favorites_only:
            query += " AND i.isFavourite = 1"

        query += """
            GROUP BY i.id
            ORDER BY i.captured_at DESC
        """

        cursor.execute(query, params)
        results = cursor.fetchall()

        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata

            images.append(
                {
                    "id": row[0],
                    "path": row[1],
                    "folder_id": str(row[2]) if row[2] else None,
                    "thumbnailPath": row[3],
                    "metadata": image_util_parse_metadata(row[4]),
                    "isTagged": bool(row[5]),
                    "isFavourite": bool(row[6]),
                    "latitude": row[7],
                    "longitude": row[8],
                    "captured_at": row[9] if row[9] else None,
                    "tags": row[10].split(",") if row[10] else None,
                }
            )

        return images

    except sqlite3.Error as e:
        logger.error(f"Error getting images by date range: {e}")
        return []
    finally:
        conn.close()


def db_get_images_near_location(
    latitude: float, longitude: float, radius_km: float = 5.0
) -> List[dict]:
    """
    Get images near a location within radius_km using bounding box approximation.

    Args:
        latitude: Center latitude (-90 to 90)
        longitude: Center longitude (-180 to 180)
        radius_km: Search radius in kilometers (default: 5km)

    Returns:
        List of image dictionaries with location data

    Note:
        Uses simple bounding box (not precise Haversine distance).
        1 degree latitude ≈ 111 km
        1 degree longitude ≈ 111 km * cos(latitude)
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        import math

        # Calculate bounding box offsets
        lat_offset = radius_km / 111.0
        cos_lat = abs(math.cos(math.radians(latitude)))
        # Clamp to avoid division by near-zero at poles
        lon_offset = radius_km / (111.0 * max(cos_lat, 0.01))

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
                i.latitude, 
                i.longitude, 
                i.captured_at,
                GROUP_CONCAT(m.name, ',') as tags
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.latitude BETWEEN ? AND ?
              AND i.longitude BETWEEN ? AND ?
              AND i.latitude IS NOT NULL 
              AND i.longitude IS NOT NULL
            GROUP BY i.id
            ORDER BY i.captured_at DESC
        """,
            (
                latitude - lat_offset,
                latitude + lat_offset,
                longitude - lon_offset,
                longitude + lon_offset,
            ),
        )

        results = cursor.fetchall()

        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata

            images.append(
                {
                    "id": row[0],
                    "path": row[1],
                    "folder_id": str(row[2]) if row[2] else None,
                    "thumbnailPath": row[3],
                    "metadata": image_util_parse_metadata(row[4]),
                    "isTagged": bool(row[5]),
                    "isFavourite": bool(row[6]),
                    "latitude": row[7],
                    "longitude": row[8],
                    "captured_at": row[9] if row[9] else None,  # SQLite returns string,
                    "tags": row[10].split(",") if row[10] else None,
                }
            )

        return images

    except sqlite3.Error as e:
        logger.error(f"Error getting images near location: {e}")
        return []
    finally:
        conn.close()


def db_get_images_by_year_month(year: int, month: int) -> List[dict]:
    """
    Get all images captured in a specific year and month.

    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)

    Returns:
        List of image dictionaries captured in the specified month
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
                i.latitude, 
                i.longitude, 
                i.captured_at,
                GROUP_CONCAT(m.name, ',') as tags
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE strftime('%Y', i.captured_at) = ?
              AND strftime('%m', i.captured_at) = ?
            GROUP BY i.id
            ORDER BY i.captured_at DESC
        """,
            (str(year).zfill(4), str(month).zfill(2)),
        )

        results = cursor.fetchall()

        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata

            images.append(
                {
                    "id": row[0],
                    "path": row[1],
                    "folder_id": str(row[2]) if row[2] else None,
                    "thumbnailPath": row[3],
                    "metadata": image_util_parse_metadata(row[4]),
                    "isTagged": bool(row[5]),
                    "isFavourite": bool(row[6]),
                    "latitude": row[7],
                    "longitude": row[8],
                    "captured_at": row[9] if row[9] else None,  # SQLite returns string,
                    "tags": row[10].split(",") if row[10] else None,
                }
            )

        return images

    except sqlite3.Error as e:
        logger.error(f"Error getting images by year/month: {e}")
        return []
    finally:
        conn.close()


def db_get_images_with_location() -> List[dict]:
    """
    Get all images that have valid GPS coordinates.
    Useful for displaying all photos on a map.

    Returns:
        List of image dictionaries that have latitude and longitude
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
                i.latitude, 
                i.longitude, 
                i.captured_at,
                GROUP_CONCAT(m.name, ',') as tags
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.latitude IS NOT NULL 
              AND i.longitude IS NOT NULL
            GROUP BY i.id
            ORDER BY i.captured_at DESC
        """
        )

        results = cursor.fetchall()

        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata

            images.append(
                {
                    "id": row[0],
                    "path": row[1],
                    "folder_id": str(row[2]) if row[2] else None,
                    "thumbnailPath": row[3],
                    "metadata": image_util_parse_metadata(row[4]),
                    "isTagged": bool(row[5]),
                    "isFavourite": bool(row[6]),
                    "latitude": row[7],
                    "longitude": row[8],
                    "captured_at": row[9] if row[9] else None,  # SQLite returns string,
                    "tags": row[10].split(",") if row[10] else None,
                }
            )

        return images

    except sqlite3.Error as e:
        logger.error(f"Error fetching images with location: {e}")
        return []
    finally:
        conn.close()


def db_get_all_images_for_memories() -> List[dict]:
    """
    Get ALL images that can be used for memories (with OR without GPS).
    Includes images with timestamps for date-based memories.

    Returns:
        List of all image dictionaries (both GPS and non-GPS images)
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
                i.latitude, 
                i.longitude, 
                i.captured_at,
                GROUP_CONCAT(m.name, ',') as tags
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            GROUP BY i.id
            ORDER BY i.captured_at DESC
        """
        )

        results = cursor.fetchall()

        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata

            images.append(
                {
                    "id": row[0],
                    "path": row[1],
                    "folder_id": str(row[2]) if row[2] else None,
                    "thumbnailPath": row[3],
                    "metadata": image_util_parse_metadata(row[4]),
                    "isTagged": bool(row[5]),
                    "isFavourite": bool(row[6]),
                    "latitude": row[7] if row[7] is not None else None,  # Can be None
                    "longitude": row[8] if row[8] is not None else None,  # Can be None
                    "captured_at": row[9] if row[9] else None,
                    "tags": row[10].split(",") if row[10] else None,
                }
            )

        return images

    except sqlite3.Error as e:
        logger.error(f"Error getting images from database: {e}")
        return []
    finally:
        conn.close()


def db_mark_images_embedded(image_ids: List[str]) -> bool:
    """Mark a batch of images as embedded in the database."""
    if not image_ids:
        return True

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        # Chunk by 500 to stay under SQLite's 999-variable limit per statement,
        # matching db_get_images_by_ids's convention.
        chunk_size = 500
        for i in range(0, len(image_ids), chunk_size):
            chunk = image_ids[i : i + chunk_size]
            placeholders = ",".join(["?"] * len(chunk))
            query = f"UPDATE images SET isEmbedded = 1 WHERE id IN ({placeholders})"
            cursor.execute(query, chunk)

        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error marking images as embedded: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
