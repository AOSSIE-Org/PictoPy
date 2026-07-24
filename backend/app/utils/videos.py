from __future__ import annotations

import os
import shutil
import uuid
import datetime
import json
import mimetypes
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
from pathlib import Path

import cv2
from PIL import Image

from app.config.settings import THUMBNAIL_IMAGES_PATH, VIDEO_FRAMES_PATH
from app.database.videos import (
    VideoRecord,
    db_bulk_insert_videos,
    db_get_video_index_by_folder_ids,
    db_get_videos_by_folder_ids,
    db_delete_videos_by_ids,
)
from app.utils.images import (
    image_util_find_folder_id_for_image,
    image_util_parse_metadata,
)
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Formats WebView2's HTML5 <video> can play; extend deliberately —
# indexing formats the player can't decode gives a broken playback UX.
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}

# path -> (stored thumbnail path, stored metadata) for videos already in the DB
IndexedVideos = Dict[str, Tuple[Optional[str], Mapping[str, Any]]]


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

        all_video_records: List[VideoRecord] = []
        all_folder_ids = []
        superseded_thumbnails: List[str] = []

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
                    path: (thumbnail_path, image_util_parse_metadata(metadata))
                    for path, thumbnail_path, metadata in (
                        db_get_video_index_by_folder_ids([folder_id])
                    )
                }

                folder_video_records = video_util_prepare_video_records(
                    video_files, folder_path_to_id, already_indexed
                )
                superseded_thumbnails.extend(
                    video_util_collect_superseded_thumbnails(
                        folder_video_records, already_indexed
                    )
                )
                all_video_records.extend(folder_video_records)

            except Exception as e:
                logger.error(f"Error processing folder {folder_path}: {e}")
                continue

        if all_folder_ids:
            video_util_remove_obsolete_videos(all_folder_ids)

        if all_video_records:
            inserted = db_bulk_insert_videos(all_video_records)
            if inserted:
                # Rows now point at the new posters, so the old ones are free
                video_util_remove_thumbnail_files(superseded_thumbnails)
            else:
                # Nothing references the posters we just wrote; the surviving
                # rows still point at their original, untouched thumbnails.
                video_util_remove_thumbnail_files(
                    record.get("thumbnailPath") for record in all_video_records
                )
            return inserted

        return True  # No videos to process is not an error
    except Exception as e:
        logger.error(f"Error processing folders: {e}")
        return False


def video_util_remove_thumbnail_files(
    thumbnail_paths: Iterable[Optional[str]],
) -> None:
    """Delete thumbnail files, tolerating ones that are already gone."""
    for thumbnail_path in thumbnail_paths:
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            continue
        try:
            os.remove(thumbnail_path)
            logger.info(f"Removed thumbnail: {thumbnail_path}")
        except OSError as e:
            logger.error(f"Error removing thumbnail {thumbnail_path}: {e}")


def video_util_collect_superseded_thumbnails(
    records: List[VideoRecord], already_indexed: IndexedVideos
) -> List[str]:
    """Posters a rescan is about to replace.

    Held back until the upsert succeeds, so a failed write never leaves a row
    pointing at a thumbnail that has already been deleted.
    """
    superseded = []
    for record in records:
        new_thumbnail = record.get("thumbnailPath")
        # Regeneration failed, so the row keeps its existing poster
        if not new_thumbnail:
            continue

        old_thumbnail, _ = already_indexed.get(record["path"], (None, {}))
        if old_thumbnail and old_thumbnail != new_thumbnail:
            superseded.append(old_thumbnail)

    return superseded


def video_util_source_is_unchanged(
    video_path: str, stored_metadata: Mapping[str, Any]
) -> bool:
    """Compare a video against the size/mtime recorded when it was indexed."""
    try:
        stats = os.stat(video_path)
    except OSError:
        return False

    if stored_metadata.get("file_size") != stats.st_size:
        return False

    return (
        stored_metadata.get("date_created")
        == datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
    )


def video_util_prepare_video_records(
    video_files: List[str],
    folder_path_to_id: Dict[str, int],
    already_indexed: Optional[IndexedVideos] = None,
) -> List[VideoRecord]:
    """
    Prepare video records with thumbnails for database insertion.
    A failed thumbnail (undecodable codec) keeps the record with thumbnailPath=None.
    """
    already_indexed = already_indexed or {}
    video_records: List[VideoRecord] = []

    for video_path in video_files:
        folder_id = image_util_find_folder_id_for_image(video_path, folder_path_to_id)

        if not folder_id:
            continue  # Skip if no matching folder ID found

        existing_thumbnail, existing_metadata = already_indexed.get(
            video_path, (None, {})
        )

        # Untouched since it was indexed and its thumbnail is still on disk:
        # regenerating would orphan the old JPEG and re-decode for nothing.
        # A file swapped in at the same path fails the fingerprint and is redone.
        if (
            existing_thumbnail
            and os.path.exists(existing_thumbnail)
            and video_util_source_is_unchanged(video_path, existing_metadata)
        ):
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
    obsolete_thumbnails = []
    for video_id, video_path, thumbnail_path in existing_db_videos:
        if not os.path.exists(video_path):
            obsolete_videos.append(video_id)
            obsolete_thumbnails.append(thumbnail_path)

    if obsolete_videos:
        # Drop the rows first: an orphaned file beats a row pointing at nothing
        db_delete_videos_by_ids(obsolete_videos)
        video_util_remove_thumbnail_files(obsolete_thumbnails)
        # The video_frames rows cascade with the video; their JPEGs don't.
        for video_id in obsolete_videos:
            video_util_remove_frame_directory(video_id)
        logger.info(f"Removed {len(obsolete_videos)} obsolete video(s) from database")

    return len(obsolete_videos)


# ============================================================================
# KEYFRAME SAMPLING - AI tagging without per-frame inference
# ============================================================================


def video_util_frame_directory(video_id: str) -> str:
    """Where a video's sampled keyframe JPEGs live."""
    return os.path.join(VIDEO_FRAMES_PATH, video_id)


def video_util_remove_frame_directory(video_id: str) -> None:
    frame_dir = video_util_frame_directory(video_id)
    if os.path.isdir(frame_dir):
        try:
            shutil.rmtree(frame_dir)
        except OSError as e:
            logger.error(f"Error removing frame directory {frame_dir}: {e}")


def video_util_get_frame_interval() -> float:
    """The user's keyframe interval, falling back to the configured default."""
    from app.config.settings import VIDEO_FRAME_INTERVAL_SECONDS
    from app.database.metadata import db_get_metadata

    try:
        metadata = db_get_metadata() or {}
        interval = metadata.get("user_preferences", {}).get("Video_Frame_Interval")
        if interval is not None:
            return float(interval)
    except Exception as e:
        logger.warning(f"Could not read frame interval preference: {e}")

    return VIDEO_FRAME_INTERVAL_SECONDS


def video_util_sample_frame_timestamps(
    duration: Optional[float], interval: float, max_frames: int
) -> List[float]:
    """Timestamps (seconds) to sample a video at.

    Frames land at chunk midpoints -- the start of a video is often a black
    leader frame, and a midpoint is the most representative moment of the
    chunk it stands for. Videos long enough to exceed max_frames get their
    interval stretched rather than their frame count grown, so inference cost
    per video is bounded regardless of length.
    """
    if not duration or duration <= 0 or interval <= 0:
        return [0.0]

    effective_interval = max(interval, duration / max_frames)
    if duration <= effective_interval:
        return [duration / 2]

    timestamps = []
    position = effective_interval / 2
    while position < duration and len(timestamps) < max_frames:
        timestamps.append(round(position, 3))
        position += effective_interval

    return timestamps or [duration / 2]


def video_util_extract_video_frames(
    video_id: str, video_path: str, interval: float
) -> List[dict]:
    """Sample a video into keyframe JPEGs on disk.

    Seeks to each timestamp rather than decoding sequentially -- that's what
    keeps a two-hour video affordable. Returns frame records ready for
    db_bulk_insert_video_frames; a frame that won't decode is skipped, not
    fatal.
    """
    from app.config.settings import (
        VIDEO_FRAME_MAX_DIMENSION,
        VIDEO_MAX_FRAMES_PER_VIDEO,
    )

    frame_dir = video_util_frame_directory(video_id)
    # Start from a clean sample: a re-tag must not mix frames from a previous
    # interval into the new set.
    video_util_remove_frame_directory(video_id)

    capture = cv2.VideoCapture(video_path)
    try:
        if not capture.isOpened():
            logger.warning(f"Could not open video for frame sampling: {video_path}")
            return []

        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = frame_count / fps if fps > 0 and frame_count > 0 else None

        timestamps = video_util_sample_frame_timestamps(
            duration, interval, VIDEO_MAX_FRAMES_PER_VIDEO
        )

        os.makedirs(frame_dir, exist_ok=True)

        frame_records = []
        for index, timestamp in enumerate(timestamps):
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = capture.read()
            if not ret or frame is None:
                continue

            frame_path = os.path.abspath(
                os.path.join(frame_dir, f"frame_{index:04d}.jpg")
            )
            try:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img.thumbnail((VIDEO_FRAME_MAX_DIMENSION, VIDEO_FRAME_MAX_DIMENSION))
                img.save(frame_path, "JPEG", quality=85)
            except Exception as e:
                logger.error(f"Error saving frame {index} of {video_path}: {e}")
                continue

            frame_records.append(
                {
                    "id": str(uuid.uuid4()),
                    "video_id": video_id,
                    "frame_path": frame_path,
                    "timestamp_sec": timestamp,
                    "frame_index": index,
                }
            )

        return frame_records
    except Exception as e:
        logger.error(f"Error sampling frames for {video_path}: {e}")
        return []
    finally:
        capture.release()


def video_util_aggregate_frame_classes(
    frame_class_ids: List[List[int]], min_support: int
) -> List[Tuple[int, int]]:
    """Roll per-frame detections up to video-level (class_id, frame_count).

    A class is only kept if it was seen in enough frames -- one detection in
    one unlucky keyframe describes the frame, not the video. Videos too short
    to have that many frames fall back to a support of 1.
    """
    if not frame_class_ids:
        return []

    counts: Dict[int, int] = {}
    for class_ids in frame_class_ids:
        for class_id in set(class_ids or []):
            counts[class_id] = counts.get(class_id, 0) + 1

    required = min_support if len(frame_class_ids) >= min_support + 1 else 1
    return sorted(
        ((class_id, count) for class_id, count in counts.items() if count >= required),
        key=lambda pair: (-pair[1], pair[0]),
    )


def video_util_process_untagged_videos() -> bool:
    """Sample and object-tag every untagged video in AI-tagging folders."""
    from app.config.settings import VIDEO_TAG_MIN_FRAME_SUPPORT
    from app.database.video_frames import (
        db_bulk_insert_video_frames,
        db_delete_frames_for_videos,
        db_get_untagged_videos,
        db_mark_videos_tagged,
        db_write_video_classes,
    )
    from app.models.ObjectClassifier import ObjectClassifier

    try:
        untagged_videos = db_get_untagged_videos()
        if not untagged_videos:
            return True

        interval = video_util_get_frame_interval()
        object_classifier = ObjectClassifier()
        total_frames = 0

        try:
            for video in untagged_videos:
                video_id = video["id"]
                frames = video_util_extract_video_frames(
                    video_id, video["path"], interval
                )

                if not frames:
                    # Undecodable files are still marked tagged, otherwise
                    # every folder sync retries them forever.
                    logger.warning(
                        f"No frames sampled from {video['path']}; tagging as empty"
                    )
                    db_mark_videos_tagged([video_id])
                    continue

                db_delete_frames_for_videos([video_id])
                db_bulk_insert_video_frames(frames)
                total_frames += len(frames)

                frame_class_ids = [
                    object_classifier.get_classes(frame["frame_path"]) or []
                    for frame in frames
                ]
                db_write_video_classes(
                    video_id,
                    video_util_aggregate_frame_classes(
                        frame_class_ids, VIDEO_TAG_MIN_FRAME_SUPPORT
                    ),
                )
                db_mark_videos_tagged([video_id])
        finally:
            object_classifier.close()

        logger.info(
            f"Video tagging pass complete. Videos: {len(untagged_videos)}, "
            f"Frames sampled: {total_frames}, Interval: {interval}s"
        )
        return True
    except Exception as e:
        logger.error(f"Error processing untagged videos: {e}")
        return False


def video_util_process_unembedded_frames() -> None:
    """Embed sampled keyframes with SigLIP2 -- the video counterpart of
    image_util_process_unembedded_images."""
    import time

    import numpy as np

    from app.config.settings import (
        SIGLIP2_ACTIVE_CHECKPOINT,
        SIGLIP2_SCORING_METADATA,
        SIGLIP2_EMBED_BATCH_SIZE,
    )
    from app.database.video_frames import (
        db_get_unembedded_video_frames,
        db_mark_video_frames_embedded,
        db_upsert_video_frame_embeddings,
    )
    from app.models.model_registry import get_siglip2_registry_keys, get_model_path
    from app.models.SigLIP2Vision import SigLIP2Vision
    from app.utils.SigLIP import siglip_util_preprocess_image

    try:
        vision_key, _ = get_siglip2_registry_keys(SIGLIP2_ACTIVE_CHECKPOINT)
        vision_model_path = get_model_path(vision_key)
        if not os.path.exists(vision_model_path):
            logger.info(
                "SigLIP2 vision model not installed; skipping frame embedding pass"
            )
            return

        unembedded_frames = db_get_unembedded_video_frames()
        if not unembedded_frames:
            return

        metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
        resolution = metadata["input_resolution"]
        model_version = metadata["model_version"]

        vision_model = SigLIP2Vision(vision_model_path)
        try:
            total_frames = len(unembedded_frames)
            embedded_count = 0
            corrupt_count = 0
            start_time = time.time()

            for i in range(0, total_frames, SIGLIP2_EMBED_BATCH_SIZE):
                batch = unembedded_frames[i : i + SIGLIP2_EMBED_BATCH_SIZE]

                good_arrays = []
                good_ids = []

                for frame in batch:
                    preprocessed = siglip_util_preprocess_image(
                        frame["frame_path"], resolution
                    )
                    if preprocessed is None:
                        corrupt_count += 1
                        continue

                    good_arrays.append(preprocessed)
                    good_ids.append(frame["id"])

                if not good_arrays:
                    continue

                stacked = np.stack(good_arrays)  # [N, 3, R, R]
                embeddings = vision_model.get_embedding(stacked)  # [N, D]

                db_upsert_video_frame_embeddings(
                    [
                        (good_ids[idx], model_version, emb)
                        for idx, emb in enumerate(embeddings)
                    ]
                )
                embedded_count += len(good_arrays)

                # Only frames that actually got an embedding row, so a frame
                # that fails to decode is retried next pass.
                db_mark_video_frames_embedded(good_ids)

            elapsed = time.time() - start_time
            logger.info(
                f"Video frame embedding pass complete. Total: {total_frames}, "
                f"Embedded: {embedded_count}, Corrupt: {corrupt_count}, "
                f"Elapsed: {elapsed:.2f}s"
            )
        finally:
            vision_model.close()

    except Exception as e:
        logger.error(f"Error embedding video frames: {e}")


def video_util_purge_frame_cache() -> int:
    """Delete the keyframe JPEGs and return the bytes reclaimed.

    Frame rows and their embeddings survive, so tags and semantic search keep
    working -- only a re-tag would need the frames extracted again.
    """
    from app.database.video_frames import db_clear_frame_paths

    reclaimed = 0
    if os.path.isdir(VIDEO_FRAMES_PATH):
        for root, _, files in os.walk(VIDEO_FRAMES_PATH):
            for file in files:
                try:
                    reclaimed += os.path.getsize(os.path.join(root, file))
                except OSError:
                    continue
        try:
            shutil.rmtree(VIDEO_FRAMES_PATH)
        except OSError as e:
            logger.error(f"Error purging frame cache: {e}")
            return 0

    db_clear_frame_paths()
    logger.info(f"Purged video frame cache, reclaimed {reclaimed} bytes")
    return reclaimed
