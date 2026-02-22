import sqlite3
from typing import List, Tuple, NamedTuple
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_sync_logger

logger = get_sync_logger(__name__)

# Type definitions
FolderId = str
FolderPath = str
FolderIdPath = Tuple[FolderId, str]


class FolderTaggingInfo(NamedTuple):
    """Represents folder tagging information"""

    folder_id: FolderId
    folder_path: FolderPath
    total_images: int
    tagged_images: int
    tagging_percentage: float


def db_get_all_folders_with_ids() -> List[FolderIdPath]:
    """
    Get all folders from the database with their IDs and paths.

    Returns:
        List of tuples containing (folder_id, folder_path)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT folder_id, folder_path FROM folders
            ORDER BY folder_path
            """
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting folders from database: {e}")
        return []
    finally:
        conn.close()


def db_check_database_connection() -> bool:
    """
    Check if the database connection is working and the folders table exists.

    Returns:
        True if connection is successful and table exists, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Check if folders table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='folders'
            """
        )
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


def db_get_tagging_progress() -> List[FolderTaggingInfo]:
    """
    Calculate tagging percentage for all folders.
    Tagging percentage = (tagged images / total images) * 100

    Returns:
        List of FolderTaggingInfo containing folder_id, folder_path, and tagging_percentage
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                f.folder_id,
                f.folder_path,
                COUNT(i.id) as total_images,
                COUNT(CASE WHEN i.isTagged = 1 THEN 1 END) as tagged_images
            FROM folders f
            LEFT JOIN images i ON f.folder_id = i.folder_id
            GROUP BY f.folder_id, f.folder_path
            """
        )

        results = cursor.fetchall()

        folder_info_list = []
        for folder_id, folder_path, total_images, tagged_images in results:
            if total_images > 0:
                tagging_percentage = (tagged_images / total_images) * 100
            else:
                tagging_percentage = 0.0

            folder_info_list.append(
                FolderTaggingInfo(
                    folder_id=folder_id,
                    folder_path=folder_path,
                    total_images=total_images,
                    tagged_images=tagged_images,
                    tagging_percentage=round(tagging_percentage, 2),
                )
            )

        return folder_info_list

    finally:
        conn.close()
