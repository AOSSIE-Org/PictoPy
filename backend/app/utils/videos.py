import os
import uuid
import json
import datetime
import cv2
from typing import Dict, List, Tuple
from pathlib import Path
from app.config.settings import VIDEOS_PATH
from app.database.videos import db_insert_video
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def video_util_ensure_dirs() -> None:
    os.makedirs(VIDEOS_PATH, exist_ok=True)


def video_util_extract_metadata(video_path: str) -> Dict:
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("Unable to open video")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()

        stats = os.stat(video_path)
        return {
            "name": os.path.basename(video_path),
            "date_created": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "width": width,
            "height": height,
            "duration": duration,
            "file_location": video_path,
            "file_size": stats.st_size,
            "item_type": "video/mp4",  # best effort; actual type resolved by player
        }
    except Exception:
        return {
            "name": os.path.basename(video_path),
            "date_created": None,
            "width": 0,
            "height": 0,
            "duration": 0,
            "file_location": video_path,
            "file_size": 0,
            "item_type": "video",
        }


def video_util_register_file(
    file_path: str, folder_id: int | None = None
) -> str | None:
    """Register a video file in the database."""
    from app.database.videos import db_get_video_by_path

    video_util_ensure_dirs()
    abs_file_path = os.path.abspath(file_path)

    existing = db_get_video_by_path(abs_file_path)
    if existing:
        logger.info(f"Video already registered: {abs_file_path}")
        return existing["id"]

    video_id = str(uuid.uuid4())
    metadata = video_util_extract_metadata(abs_file_path)

    ok = db_insert_video(
        {
            "id": video_id,
            "path": abs_file_path,
            "folder_id": folder_id,
            "thumbnailPath": None,
            "metadata": json.dumps(metadata),
        }
    )
    return video_id if ok else None


def video_util_is_valid_video(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".mpeg", ".mpg"}
    return ext in allowed


def video_util_get_videos_from_folder(
    folder_path: str, recursive: bool = True
) -> List[str]:
    videos: List[str] = []
    if recursive:
        for root, _, files in os.walk(folder_path):
            for f in files:
                p = os.path.join(root, f)
                if video_util_is_valid_video(p):
                    videos.append(p)
    else:
        try:
            for f in os.listdir(folder_path):
                p = os.path.join(folder_path, f)
                if os.path.isfile(p) and video_util_is_valid_video(p):
                    videos.append(p)
        except OSError:
            pass
    return videos


essential_tuple = Tuple[str, int, bool]


def video_util_process_folder_videos(folder_data: List[essential_tuple]) -> bool:
    try:
        video_util_ensure_dirs()
        for path, folder_id, recursive in folder_data:
            file_list = video_util_get_videos_from_folder(path, recursive)
            for fp in file_list:
                try:
                    video_util_register_file(fp, folder_id)
                except Exception:
                    continue
        return True
    except Exception:
        return False
