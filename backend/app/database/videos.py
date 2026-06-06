# Standard library imports
import sqlite3
from typing import Any, List, Mapping, TypedDict, Union

# App-specific imports
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Type aliases
VideoId = str
VideoPath = str
FolderId = Union[int, None]


class VideoRecord(TypedDict):
    id: VideoId
    path: VideoPath
    folder_id: FolderId
    thumbnailPath: Union[str, None]
    metadata: Union[Mapping[str, Any], str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_videos_table() -> None:
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            path VARCHAR UNIQUE,
            folder_id INTEGER,
            thumbnailPath TEXT,
            metadata TEXT,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE SET NULL
        )
        """
    )

    conn.commit()
    conn.close()


def db_insert_video(record: VideoRecord) -> bool:
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO videos (id, path, folder_id, thumbnailPath, metadata)
            VALUES (:id, :path, :folder_id, :thumbnailPath, :metadata)
            ON CONFLICT(path) DO UPDATE SET
                folder_id=excluded.folder_id,
                thumbnailPath=excluded.thumbnailPath,
                metadata=excluded.metadata
            """,
            record,
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting video record: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_videos() -> List[dict]:
    """Get all videos from database, filtering out videos whose files no longer exist."""
    import os

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata
            FROM videos
            ORDER BY path
            """
        )
        rows = cursor.fetchall()
        videos = []
        deleted_ids = []

        for v_id, path, folder_id, thumb, metadata in rows:
            if not os.path.exists(path):
                deleted_ids.append(v_id)
                continue

            videos.append(
                {
                    "id": v_id,
                    "path": path,
                    "folder_id": str(folder_id) if folder_id is not None else "",
                    "thumbnailPath": thumb,
                    "metadata": metadata,
                }
            )

        if deleted_ids:
            cursor.execute(
                f"DELETE FROM videos WHERE id IN ({','.join('?' * len(deleted_ids))})",
                deleted_ids,
            )
            conn.commit()
            logger.info(f"Removed {len(deleted_ids)} deleted video(s) from database")

        return videos
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return []
    finally:
        conn.close()


def db_get_video_by_path(path: str) -> dict | None:
    """Get a video record by its file path."""
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, path, folder_id, thumbnailPath, metadata
            FROM videos
            WHERE path = ?
            """,
            (path,),
        )
        row = cursor.fetchone()
        if row:
            v_id, path, folder_id, thumb, metadata = row
            return {
                "id": v_id,
                "path": path,
                "folder_id": str(folder_id) if folder_id is not None else "",
                "thumbnailPath": thumb,
                "metadata": metadata,
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching video by path {path}: {e}")
        return None
    finally:
        conn.close()


def db_delete_video_by_id(video_id: VideoId) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
