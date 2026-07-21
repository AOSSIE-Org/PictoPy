from __future__ import annotations

import os
import uuid
import datetime
import json
import mimetypes
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import cv2
from PIL import Image

from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.database.videos import (
    db_bulk_insert_videos,
    db_get_videos_by_folder_ids,
    db_delete_videos_by_ids,
)
from app.utils.images import image_util_find_folder_id_for_image
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Formats WebView2's HTML5 <video> can play; extend deliberately —
# indexing formats the player can't decode gives a broken playback UX.
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}


def video_util_process_folder_videos(folder_data: List[Tuple[str, int, bool]]) -> bool:
    """Main function to process videos in multiple folders based on provided folder data.

    Args:
        folder_data: List of tuples containing (folder_path, folder_id, recursive)

    Returns:
        bool: True if all folders processed successfully, False otherwise
    """
    try:
        # Ensure thumbnail directory exists
        os.makedirs(THUMBNAIL_IMAGES_PATH, exist_ok=True)

        all_video_records = []
        all_folder_ids = []

        for folder_path, folder_id, recursive in folder_data:
            try:
                all_folder_ids.append(folder_id)

                video_files = video_util_get_videos_from_folder(folder_path, recursive)

                if not video_files:
                    continue

                folder_path_to_id = {os.path.abspath(folder_path): folder_id}

                # What this folder already has indexed, so unchanged files are
                # left alone instead of being re-decoded into a fresh thumbnail.
                already_indexed = {
                    path: thumbnail_path
                    for _, path, thumbnail_path in db_get_videos_by_folder_ids(
                        [folder_id]
                    )
                }

                folder_video_records = video_util_prepare_video_records(
                    video_files, folder_path_to_id, already_indexed
                )
                all_video_records.extend(folder_video_records)

            except Exception as e:
                logger.error(f"Error processing folder {folder_path}: {e}")
                continue

        if all_folder_ids:
            video_util_remove_obsolete_videos(all_folder_ids)

        if all_video_records:
            return db_bulk_insert_videos(all_video_records)

        return True  # No videos to process is not an error
    except Exception as e:
        logger.error(f"Error processing folders: {e}")
        return False


def video_util_prepare_video_records(
    video_files: List[str],
    folder_path_to_id: Dict[str, int],
    already_indexed: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict]:
    """
    Prepare video records with thumbnails for database insertion.
    A failed thumbnail (undecodable codec) keeps the record with thumbnailPath=None.
    """
    already_indexed = already_indexed or {}
    video_records = []

    for video_path in video_files:
        folder_id = image_util_find_folder_id_for_image(video_path, folder_path_to_id)

        if not folder_id:
            continue  # Skip if no matching folder ID found

        # Already indexed and its thumbnail is still on disk: regenerating would
        # orphan the old JPEG and re-decode the file for nothing.
        existing_thumbnail = already_indexed.get(video_path)
        if existing_thumbnail and os.path.exists(existing_thumbnail):
            continue

        video_id = str(uuid.uuid4())
        thumbnail_name = f"thumbnail_{video_id}.jpg"
        thumbnail_path = os.path.abspath(
            os.path.join(THUMBNAIL_IMAGES_PATH, thumbnail_name)
        )

        # One capture serves both the poster frame and the metadata read
        capture = cv2.VideoCapture(video_path)
        try:
            if not video_util_generate_thumbnail(
                video_path, thumbnail_path, capture=capture
            ):
                thumbnail_path = None

            metadata = video_util_extract_metadata(video_path, capture=capture)
        finally:
            capture.release()

        video_records.append(
            {
                "id": video_id,
                "path": video_path,
                "folder_id": folder_id,
                "thumbnailPath": thumbnail_path,
                "metadata": json.dumps(metadata),
                "isTagged": False,
                "captured_at": metadata.get("date_created"),
            }
        )

    return video_records


def video_util_get_videos_from_folder(
    folder_path: str, recursive: bool = True
) -> List[str]:
    """Get all video files from a folder.

    Args:
        folder_path: Path to the folder to scan
        recursive: If True, scan subfolders recursively. If False, only scan direct children.

    Returns:
        List of video file paths
    """
    video_files = []

    if recursive:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if video_util_is_valid_video(file_path):
                    video_files.append(file_path)
    else:
        try:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and video_util_is_valid_video(file_path):
                    video_files.append(file_path)
        except OSError as e:
            logger.error(f"Error reading folder {folder_path}: {e}")

    return video_files


def video_util_is_valid_video(file_path: str) -> bool:
    """Check extension and non-empty size. No decode check here — thumbnail
    generation is the de facto decoder probe and its failure is non-fatal."""
    if Path(file_path).suffix.lower() not in VIDEO_EXTENSIONS:
        return False

    try:
        return os.path.getsize(file_path) > 0
    except OSError:
        return False


def video_util_generate_thumbnail(
    video_path: str,
    thumbnail_path: str,
    size: Tuple[int, int] = (600, 600),
    capture: Optional[cv2.VideoCapture] = None,
) -> bool:
    """Generate a poster-frame thumbnail for a single video.

    Pass an open `capture` to share one decoder with metadata extraction.
    """
    owns_capture = capture is None
    cap = capture
    try:
        if cap is None:
            cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False

        # Poster frame at ~1 second or 10% in, whichever is earlier
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        target = int(min(fps, frame_count * 0.1)) if fps > 0 and frame_count > 0 else 0

        if target > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        ret, frame = cap.read()
        if not ret and target > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if not ret or frame is None:
            return False

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img.thumbnail(size)
        img.save(thumbnail_path, "JPEG")  # Always save thumbnails as JPEG
        return True
    except Exception as e:
        logger.error(f"Error generating thumbnail for {video_path}: {e}")
        return False
    finally:
        if owns_capture and cap is not None:
            cap.release()


def video_util_extract_metadata(
    video_path: str, capture: Optional[cv2.VideoCapture] = None
) -> dict:
    """Extract metadata for a given video file (cv2 props + file stats).

    Pass an open `capture` to share one decoder with thumbnail generation.
    """
    metadata = {
        "name": os.path.basename(video_path),
        "date_created": None,
        "width": 0,
        "height": 0,
        "duration": None,
        "fps": None,
        "file_location": video_path,
        "file_size": 0,
        "item_type": mimetypes.guess_type(video_path)[0] or "video/unknown",
    }

    try:
        stats = os.stat(video_path)
        metadata["file_size"] = stats.st_size
        metadata["date_created"] = datetime.datetime.fromtimestamp(
            stats.st_mtime
        ).isoformat()
    except OSError as e:
        logger.error(f"Error reading file stats for {video_path}: {e}")
        return metadata

    owns_capture = capture is None
    cap = capture
    try:
        if cap is None:
            cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if fps > 0:
                metadata["fps"] = round(fps, 3)
                if frame_count > 0:
                    metadata["duration"] = round(frame_count / fps, 3)
    except Exception as e:
        logger.error(f"Error extracting video metadata for {video_path}: {e}")
    finally:
        if owns_capture and cap is not None:
            cap.release()

    return metadata


def video_util_remove_obsolete_videos(folder_id_list: List[int]) -> int:
    """
    Remove obsolete videos that no longer exist in the filesystem.

    Args:
        folder_id_list: List of folder IDs to check for obsolete videos

    Returns:
        Number of obsolete videos removed
    """
    existing_db_videos = db_get_videos_by_folder_ids(folder_id_list)

    obsolete_videos = []
    for video_id, video_path, thumbnail_path in existing_db_videos:
        if not os.path.exists(video_path):
            obsolete_videos.append(video_id)
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    logger.info(f"Removed obsolete thumbnail: {thumbnail_path}")
                except OSError as e:
                    logger.error(f"Error removing thumbnail {thumbnail_path}: {e}")

    if obsolete_videos:
        db_delete_videos_by_ids(obsolete_videos)
        logger.info(f"Removed {len(obsolete_videos)} obsolete video(s) from database")

    return len(obsolete_videos)
