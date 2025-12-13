# Standard library imports
import sqlite3
from typing import Any, List, Mapping, Tuple, TypedDict, Union, Optional
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
            latitude REAL,
            longitude REAL,
            captured_at DATETIME,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    # Create indexes for Memories feature queries
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_images_latitude ON images(latitude)"
    )
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


def db_migrate_add_memories_columns() -> None:
    """
    Add Memories feature columns to existing images table if they don't exist.
    This function handles backward compatibility for existing databases.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        # Check if images table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
        if not cursor.fetchone():
            logger.info("Images table does not exist yet, will be created by db_create_images_table()")
            conn.close()
            return
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(images)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns
        changes_made = False
        
        if 'latitude' not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN latitude REAL")
            logger.info("Added column: latitude")
            changes_made = True
        
        if 'longitude' not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN longitude REAL")
            logger.info("Added column: longitude")
            changes_made = True
        
        if 'captured_at' not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN captured_at DATETIME")
            logger.info("Added column: captured_at")
            changes_made = True
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_latitude ON images(latitude)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_longitude ON images(longitude)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_captured_at ON images(captured_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_favourite_captured_at ON images(isFavourite, captured_at)")
        
        if changes_made:
            logger.info("Memories feature columns migration completed")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error during Memories columns migration: {e}")
        conn.rollback()
    finally:
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
                    "captured_at": captured_at if captured_at else None,  # SQLite returns string
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


# ============================================================================
# MEMORIES FEATURE - Location and Time-based Queries
# ============================================================================


def db_get_images_by_date_range(
    start_date: datetime, 
    end_date: datetime,
    include_favorites_only: bool = False
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
            
            images.append({
                "id": row[0],
                "path": row[1],
                "folder_id": str(row[2]) if row[2] else None,
                "thumbnailPath": row[3],
                "metadata": image_util_parse_metadata(row[4]),
                "isTagged": bool(row[5]),
                "isFavourite": bool(row[6]),
                "latitude": row[7],
                "longitude": row[8],
                "captured_at": row[9] if row[9] else None ,
                "tags": row[10].split(',') if row[10] else None
            })
        
        return images
        
    except Exception as e:
        logger.error(f"Error getting images by date range: {e}")
        return []
    finally:
        conn.close()


def db_get_images_near_location(
    latitude: float, 
    longitude: float, 
    radius_km: float = 5.0
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
        lon_offset = radius_km / (111.0 * abs(math.cos(math.radians(latitude))))
        
        cursor.execute("""
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
        """, (
            latitude - lat_offset, 
            latitude + lat_offset,
            longitude - lon_offset, 
            longitude + lon_offset
        ))
        
        results = cursor.fetchall()
        
        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata
            
            images.append({
                "id": row[0],
                "path": row[1],
                "folder_id": str(row[2]) if row[2] else None,
                "thumbnailPath": row[3],
                "metadata": image_util_parse_metadata(row[4]),
                "isTagged": bool(row[5]),
                "isFavourite": bool(row[6]),
                "latitude": row[7],
                "longitude": row[8],
                "captured_at": row[9] if row[9] else None , # SQLite returns string,
                "tags": row[10].split(',') if row[10] else None
            })
        
        return images
        
    except Exception as e:
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
        cursor.execute("""
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
        """, (str(year).zfill(4), str(month).zfill(2)))
        
        results = cursor.fetchall()
        
        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata
            
            images.append({
                "id": row[0],
                "path": row[1],
                "folder_id": str(row[2]) if row[2] else None,
                "thumbnailPath": row[3],
                "metadata": image_util_parse_metadata(row[4]),
                "isTagged": bool(row[5]),
                "isFavourite": bool(row[6]),
                "latitude": row[7],
                "longitude": row[8],
                "captured_at": row[9] if row[9] else None , # SQLite returns string,
                "tags": row[10].split(',') if row[10] else None
            })
        
        return images
        
    except Exception as e:
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
        cursor.execute("""
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
        """)
        
        results = cursor.fetchall()
        
        images = []
        for row in results:
            from app.utils.images import image_util_parse_metadata
            
            images.append({
                "id": row[0],
                "path": row[1],
                "folder_id": str(row[2]) if row[2] else None,
                "thumbnailPath": row[3],
                "metadata": image_util_parse_metadata(row[4]),
                "isTagged": bool(row[5]),
                "isFavourite": bool(row[6]),
                "latitude": row[7],
                "longitude": row[8],
                "captured_at": row[9] if row[9] else None , # SQLite returns string,
                "tags": row[10].split(',') if row[10] else None
            })
        
        return images
        
    except Exception as e:
        logger.error(f"Error getting images with location: {e}")
        return []
    finally:
        conn.close()
