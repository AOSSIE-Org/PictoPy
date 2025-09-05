"""
Images Database Module

This module provides database operations for image management in PictoPy.
It handles the creation, querying, and manipulation of image records and
their associated tags in the SQLite database.

Key Features:
- Image table creation and schema management
- Bulk image insertion for efficient data loading
- Image retrieval with tag associations
- Untagged image identification for AI processing
- Image deletion and cleanup operations
- Tag relationship management

Database Schema:
- images: Main table storing image metadata
- image_classes: Junction table linking images to detected object classes
"""

# Standard library imports
import sqlite3
from typing import List, Tuple, TypedDict

# Application imports
from app.config.settings import DATABASE_PATH

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

# Type aliases for better code readability
ImageId = str      # Unique identifier for images
ImagePath = str    # File system path to image
FolderId = str     # Unique identifier for folders
ClassId = int      # Object detection class identifier


class ImageRecord(TypedDict):
    """
    Type definition for image records in the database.
    
    Represents the complete structure of an image record including
    all metadata and processing status information.
    """
    id: ImageId           # Unique image identifier
    path: ImagePath       # File system path to the image
    folder_id: FolderId   # ID of the containing folder
    thumbnailPath: str    # Path to the image thumbnail
    metadata: str         # JSON string containing image metadata
    isTagged: bool        # Flag indicating if image has been processed for tags


# Type alias for image-class relationship pairs
ImageClassPair = Tuple[ImageId, ClassId]


# =============================================================================
# DATABASE SCHEMA CREATION
# =============================================================================

def db_create_images_table() -> None:
    """
    Create the images and image_classes tables in the database.
    
    This function sets up the database schema for image storage including:
    - Main images table with metadata and processing status
    - Junction table for image-tag relationships
    - Proper foreign key constraints and cascading deletes
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create main images table with comprehensive metadata
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,                    -- Unique image identifier
            path VARCHAR UNIQUE,                    -- File system path (unique)
            folder_id INTEGER,                      -- Reference to containing folder
            thumbnailPath TEXT UNIQUE,              -- Thumbnail path (unique)
            metadata TEXT,                          -- JSON metadata string
            isTagged BOOLEAN DEFAULT 0,             -- AI processing status flag
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    # Create junction table for many-to-many image-tag relationships
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS image_classes (
            image_id TEXT,                          -- Reference to image
            class_id INTEGER,                       -- Reference to object class
            PRIMARY KEY (image_id, class_id),       -- Composite primary key
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
            FOREIGN KEY (class_id) REFERENCES mappings(class_id) ON DELETE CASCADE
        )
    """
    )

    # Commit changes and close connection
    conn.commit()
    conn.close()


# =============================================================================
# IMAGE DATA OPERATIONS
# =============================================================================

def db_bulk_insert_images(image_records: List[ImageRecord]) -> bool:
    """
    Insert multiple image records in a single database transaction.
    
    This function efficiently inserts multiple image records using a single
    database transaction for optimal performance. Uses INSERT OR IGNORE to
    handle duplicate records gracefully.
    
    Args:
        image_records: List of ImageRecord dictionaries to insert
        
    Returns:
        bool: True if insertion was successful, False otherwise
    """
    # Handle empty input gracefully
    if not image_records:
        return True

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Use executemany for efficient bulk insertion
        cursor.executemany(
            """
            INSERT OR IGNORE INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged)
        """,
            image_records,
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
    Retrieve all images from the database with their associated tags.
    
    This function performs an optimized query that joins images with their tags
    in a single database operation. It groups the results by image ID and
    aggregates all tags for each image.
    
    Returns:
        List[dict]: List of image dictionaries containing:
            - id: Image identifier
            - path: File system path
            - folder_id: Containing folder ID
            - thumbnailPath: Thumbnail file path
            - metadata: JSON metadata string
            - isTagged: Processing status flag
            - tags: List of associated tag names (or None if no tags)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Optimized query to get all images with their tags in one operation
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

        # Group results by image ID to aggregate tags
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
            # Initialize image record if not seen before
            if image_id not in images_dict:
                images_dict[image_id] = {
                    "id": image_id,
                    "path": path,
                    "folder_id": folder_id,
                    "thumbnailPath": thumbnail_path,
                    "metadata": metadata,
                    "isTagged": bool(is_tagged),
                    "tags": [],
                }

            # Add tag to the image's tag list if it exists
            if tag_name:
                images_dict[image_id]["tags"].append(tag_name)

        # Convert dictionary to list and normalize empty tag lists
        images = []
        for image_data in images_dict.values():
            # Set tags to None if no tags were found (cleaner API response)
            if not image_data["tags"]:
                image_data["tags"] = None
            images.append(image_data)

        # Sort images by path for consistent ordering
        images.sort(key=lambda x: x["path"])

        return images

    except Exception as e:
        print(f"Error getting all images: {e}")
        return []
    finally:
        conn.close()


def db_get_untagged_images() -> List[ImageRecord]:
    """
    Find all images that require AI tagging processing.
    
    This function identifies images that need to be processed by the AI tagging
    system. It returns images where:
    - The containing folder has AI tagging enabled
    - The image has not yet been processed (isTagged = False)
    
    This is typically used by background processing services to identify
    work items for AI analysis.

    Returns:
        List[ImageRecord]: List of image records that need AI processing
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Query for images that need AI tagging
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

        # Convert query results to ImageRecord format
        untagged_images = []
        for image_id, path, folder_id, thumbnail_path, metadata in results:
            untagged_images.append(
                {
                    "id": image_id,
                    "path": path,
                    "folder_id": folder_id,
                    "thumbnailPath": thumbnail_path,
                    "metadata": metadata,
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
