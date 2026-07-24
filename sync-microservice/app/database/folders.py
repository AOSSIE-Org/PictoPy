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
    """Represents folder tagging and semantic-embedding information.

    Percentages are over images and videos combined, so a video-only folder
    still reports real progress. The raw per-medium counts are exposed so the
    frontend can aggregate them however it needs.
    """

    folder_id: FolderId
    folder_path: FolderPath
    tagging_percentage: float
    embedding_percentage: float
    total_images: int
    tagged_images: int
    embedded_images: int
    total_videos: int
    tagged_videos: int
    embedded_videos: int
    ai_tagging: bool


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
    Calculate tagging and semantic-embedding percentages for all folders.
    Each percentage = (processed media / total media) * 100, counting images
    and videos together.

    Returns:
        List of FolderTaggingInfo with percentages, raw per-medium counts, and
        each folder's AI_Tagging flag
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # COUNT(DISTINCT ...) because joining both media tables multiplies the
        # rows. embedded_videos is a correlated subquery: a video is "embedded"
        # once tagged with no unembedded frames left -- a zero-frame
        # (undecodable) video counts as embedded so it never stalls the bar.
        cursor.execute(
            """
            SELECT
                f.folder_id,
                f.folder_path,
                f.AI_Tagging,
                COUNT(DISTINCT i.id) as total_images,
                COUNT(DISTINCT CASE WHEN i.isTagged = 1 THEN i.id END)
                    as tagged_images,
                COUNT(DISTINCT CASE WHEN i.isEmbedded = 1 THEN i.id END)
                    as embedded_images,
                COUNT(DISTINCT v.id) as total_videos,
                COUNT(DISTINCT CASE WHEN v.isTagged = 1 THEN v.id END)
                    as tagged_videos,
                (
                    SELECT COUNT(*)
                    FROM videos v2
                    WHERE v2.folder_id = f.folder_id
                      AND v2.isTagged = 1
                      AND NOT EXISTS (
                          SELECT 1 FROM video_frames vf
                          WHERE vf.video_id = v2.id AND vf.isEmbedded = 0
                      )
                ) as embedded_videos
            FROM folders f
            LEFT JOIN images i ON f.folder_id = i.folder_id
            LEFT JOIN videos v ON f.folder_id = v.folder_id
            GROUP BY f.folder_id, f.folder_path, f.AI_Tagging
            """
        )

        results = cursor.fetchall()

        folder_info_list = []
        for (
            folder_id,
            folder_path,
            ai_tagging,
            total_images,
            tagged_images,
            embedded_images,
            total_videos,
            tagged_videos,
            embedded_videos,
        ) in results:
            # Percentages are over images and videos together.
            total_media = total_images + total_videos
            if total_media > 0:
                tagging_percentage = (tagged_images + tagged_videos) / total_media * 100
                embedding_percentage = (
                    (embedded_images + embedded_videos) / total_media * 100
                )
            else:
                tagging_percentage = 0.0
                embedding_percentage = 0.0

            folder_info_list.append(
                FolderTaggingInfo(
                    folder_id=folder_id,
                    folder_path=folder_path,
                    tagging_percentage=round(tagging_percentage, 2),
                    embedding_percentage=round(embedding_percentage, 2),
                    total_images=total_images,
                    tagged_images=tagged_images,
                    embedded_images=embedded_images,
                    total_videos=total_videos,
                    tagged_videos=tagged_videos,
                    embedded_videos=embedded_videos,
                    ai_tagging=bool(ai_tagging),
                )
            )

        return folder_info_list

    finally:
        conn.close()
