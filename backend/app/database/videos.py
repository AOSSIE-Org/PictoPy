# Standard library imports
import sqlite3
from typing import Any, List, Mapping, Optional, Tuple, TypedDict, Union
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
VideoId = str
VideoPath = str
FolderId = str


class VideoRecord(TypedDict, total=False):
    """Represents the full videos table structure"""

    id: VideoId
    path: VideoPath
    folder_id: FolderId
    thumbnailPath: Optional[str]
    metadata: Union[Mapping[str, Any], str]
    isTagged: bool
    isFavourite: bool
    captured_at: Optional[datetime]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    # Ensure ON DELETE CASCADE and other FKs are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_videos_table() -> None:
    conn = _connect()
    cursor = conn.cursor()

    # Videos are kept separate from images by design; isTagged is reserved
    # for future AI video tagging. thumbnailPath is nullable: videos whose
    # codec OpenCV cannot decode are still indexed (frontend shows a placeholder).
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            path VARCHAR UNIQUE,
            folder_id INTEGER,
            thumbnailPath TEXT UNIQUE,
            metadata TEXT,
            isTagged BOOLEAN DEFAULT 0,
            isFavourite BOOLEAN DEFAULT 0,
            captured_at DATETIME,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_videos_captured_at ON videos(captured_at)"
    )

    conn.commit()
    conn.close()


def db_bulk_insert_videos(video_records: List[VideoRecord]) -> bool:
    """Insert multiple video records in a single transaction."""
    if not video_records:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """
            INSERT INTO videos (id, path, folder_id, thumbnailPath, metadata, isTagged, captured_at)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata, :isTagged, :captured_at)
            ON CONFLICT(path) DO UPDATE SET
                folder_id=excluded.folder_id,
                thumbnailPath=COALESCE(excluded.thumbnailPath, videos.thumbnailPath),
                metadata=excluded.metadata,
                isTagged=CASE
                    WHEN excluded.isTagged THEN 1
                    ELSE videos.isTagged
                END,
                captured_at=COALESCE(excluded.captured_at, videos.captured_at)
            """,
            video_records,
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting video records: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_videos() -> List[dict]:
    """
    Get all videos from the database.

    Returns:
        List of dictionaries containing all video data
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, isTagged, isFavourite, captured_at
            FROM videos
            ORDER BY path
            """
        )

        results = cursor.fetchall()

        videos = []
        for (
            video_id,
            path,
            folder_id,
            thumbnail_path,
            metadata,
            is_tagged,
            is_favourite,
            captured_at,
        ) in results:
            from app.utils.images import image_util_parse_metadata

            videos.append(
                {
                    "id": video_id,
                    "path": path,
                    "folder_id": str(folder_id),
                    "thumbnailPath": thumbnail_path,
                    "metadata": image_util_parse_metadata(metadata),
                    "isTagged": bool(is_tagged),
                    "isFavourite": bool(is_favourite),
                    "captured_at": captured_at if captured_at else None,
                    "tags": None,
                }
            )

        return videos

    except sqlite3.Error as e:
        logger.error(f"Error getting all videos: {e}")
        return []
    finally:
        conn.close()


def db_get_videos_by_folder_ids(
    folder_ids: List[int],
) -> List[Tuple[VideoId, VideoPath, str]]:
    """
    Get all videos that belong to the specified folder IDs.

    Args:
        folder_ids: List of folder IDs to search for videos

    Returns:
        List of tuples containing (video_id, video_path, thumbnail_path)
    """
    if not folder_ids:
        return []

    conn = _connect()
    cursor = conn.cursor()

    try:
        placeholders = ",".join("?" for _ in folder_ids)
        cursor.execute(
            f"""
            SELECT id, path, thumbnailPath
            FROM videos
            WHERE folder_id IN ({placeholders})
            """,
            folder_ids,
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error getting videos by folder IDs: {e}")
        return []
    finally:
        conn.close()


def db_delete_videos_by_ids(video_ids: List[VideoId]) -> bool:
    """
    Delete multiple videos from the database by their IDs.

    Args:
        video_ids: List of video IDs to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    if not video_ids:
        return True

    conn = _connect()
    cursor = conn.cursor()

    try:
        placeholders = ",".join("?" for _ in video_ids)
        cursor.execute(
            f"DELETE FROM videos WHERE id IN ({placeholders})",
            video_ids,
        )
        conn.commit()
        logger.info(f"Deleted {cursor.rowcount} obsolete video(s) from database")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error deleting videos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_toggle_video_favourite_status(video_id: str) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM videos WHERE id = ?", (video_id,))
        if not cursor.fetchone():
            return False
        cursor.execute(
            """
            UPDATE videos
            SET isFavourite = CASE WHEN isFavourite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (video_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_video_by_id(video_id: str) -> Optional[dict]:
    """
    Get a single video by ID with its favorite status.
    """
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata, isTagged, isFavourite
            FROM videos
            WHERE id = ?
        """,
            (video_id,),
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
