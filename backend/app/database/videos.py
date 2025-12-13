# Standard library imports
import sqlite3
from typing import Any, List, Mapping, TypedDict, Union, Optional

# App-specific imports
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Type definitions
VideoId = str
VideoPath = str
FolderId = str


class VideoRecord(TypedDict):
    """Represents the full videos table structure"""
    id: VideoId
    path: VideoPath
    folder_id: FolderId
    thumbnailPath: str
    metadata: Union[Mapping[str, Any], str]
    duration: Optional[float]  # Duration in seconds
    width: Optional[int]
    height: Optional[int]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_videos_table() -> None:
    """Create the videos table if it doesn't exist."""
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            path VARCHAR UNIQUE,
            folder_id TEXT,
            thumbnailPath TEXT,
            metadata TEXT,
            duration REAL,
            width INTEGER,
            height INTEGER,
            isFavourite BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    conn.close()
    logger.info("Videos table created successfully")


def db_bulk_insert_videos(video_records: List[VideoRecord]) -> bool:
    """Insert multiple video records in a single transaction."""
    if not video_records:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO videos (id, path, folder_id, thumbnailPath, metadata, duration, width, height)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :duration, :width, :height)
            """,
            video_records
        )
        conn.commit()
        logger.info(f"Inserted {cursor.rowcount} videos")
        return True
    except Exception as e:
        logger.error(f"Error bulk inserting videos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_videos() -> List[dict]:
    """Get all videos from the database."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, duration, width, height, isFavourite
            FROM videos
            ORDER BY created_at DESC
            """
        )
        
        columns = ['id', 'path', 'folder_id', 'thumbnailPath', 'metadata', 'duration', 'width', 'height', 'isFavourite']
        videos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return videos
    except Exception as e:
        logger.error(f"Error getting all videos: {e}")
        return []
    finally:
        conn.close()


def db_get_videos_by_folder_ids(folder_ids: List[int]) -> List[dict]:
    """Get videos from specific folders."""
    if not folder_ids:
        return []

    conn = _connect()
    cursor = conn.cursor()

    try:
        placeholders = ','.join('?' * len(folder_ids))
        cursor.execute(
            f"""
            SELECT id, path, folder_id, thumbnailPath, metadata, duration, width, height, isFavourite
            FROM videos
            WHERE folder_id IN ({placeholders})
            ORDER BY created_at DESC
            """,
            folder_ids
        )
        
        columns = ['id', 'path', 'folder_id', 'thumbnailPath', 'metadata', 'duration', 'width', 'height', 'isFavourite']
        videos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return videos
    except Exception as e:
        logger.error(f"Error getting videos by folder IDs: {e}")
        return []
    finally:
        conn.close()


def db_get_video_by_id(video_id: str) -> Optional[dict]:
    """Get a single video by ID."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, duration, width, height, isFavourite
            FROM videos
            WHERE id = ?
            """,
            (video_id,)
        )
        
        row = cursor.fetchone()
        if row:
            columns = ['id', 'path', 'folder_id', 'thumbnailPath', 'metadata', 'duration', 'width', 'height', 'isFavourite']
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Error getting video by ID: {e}")
        return None
    finally:
        conn.close()


def db_toggle_video_favourite_status(video_id: str) -> bool:
    """Toggle the favourite status of a video."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE videos
            SET isFavourite = NOT isFavourite
            WHERE id = ?
            """,
            (video_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error toggling video favourite status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_delete_videos_by_ids(video_ids: List[str]) -> int:
    """Delete videos by their IDs."""
    if not video_ids:
        return 0

    conn = _connect()
    cursor = conn.cursor()

    try:
        placeholders = ','.join('?' * len(video_ids))
        cursor.execute(
            f"DELETE FROM videos WHERE id IN ({placeholders})",
            video_ids
        )
        conn.commit()
        deleted_count = cursor.rowcount
        logger.info(f"Deleted {deleted_count} videos")
        return deleted_count
    except Exception as e:
        logger.error(f"Error deleting videos: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def db_video_exists(video_path: str) -> bool:
    """Check if a video already exists in the database."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM videos WHERE path = ?", (video_path,))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking video existence: {e}")
        return False
    finally:
        conn.close()


def db_get_favourite_videos() -> List[dict]:
    """Get all favourite videos from the database."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, duration, width, height, isFavourite
            FROM videos
            WHERE isFavourite = 1
            ORDER BY created_at DESC
            """
        )
        
        columns = ['id', 'path', 'folder_id', 'thumbnailPath', 'metadata', 'duration', 'width', 'height', 'isFavourite']
        videos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return videos
    except Exception as e:
        logger.error(f"Error getting favourite videos: {e}")
        return []
    finally:
        conn.close()
