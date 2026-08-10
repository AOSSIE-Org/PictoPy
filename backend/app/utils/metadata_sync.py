"""
Writing what PictoPy knows about a photo into the photo itself.

Runs as a batch rather than on every change: each write touches one of the
user's original files, and doing that once per edit would multiply the risk for
no benefit. The database stays authoritative for speed; the file is what
survives PictoPy being uninstalled.
"""

import datetime
import os
from typing import Any, Dict, List, Mapping, Optional

from app.database.metadata import db_get_metadata
from app.database.metadata_sync import (
    SyncCandidate,
    db_count_images_pending_metadata_sync,
    db_get_images_pending_metadata_sync,
    db_mark_metadata_synced,
)
from app.logging.setup_logging import get_logger
from app.schemas.user_preferences import MetadataPreferences
from app.utils.self_write import self_write_util_replace
from app.utils.xmp_packet import (
    FaceRegion,
    PhotoMetadata,
    UnreadablePacketError,
    xmp_packet_applied_dimensions,
    xmp_packet_build,
    xmp_packet_orient_region,
)
from app.utils.xmp_segments import (
    UnsupportedImageError,
    xmp_segments_read,
    xmp_segments_write,
)

logger = get_logger(__name__)

# A favourite is a flag, but xmp:Rating is a scale, so it maps to the top of it.
FAVOURITE_RATING = 5

# Keeps our keywords identifiable in a tree a user may already be organising by
# hand, which a flat name would not be.
PERSON_KEYWORD_ROOT = "People"


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def metadata_util_build_packet_metadata(
    candidate: SyncCandidate, written_at: Optional[str] = None
) -> PhotoMetadata:
    """
    Turn one photo's database rows into the properties its packet should carry.

    Only keys PictoPy is prepared to own are set. A key left out is a property
    left alone in the file, which is how another application's work survives.
    """
    blob: Mapping[str, Any] = candidate.get("metadata") or {}
    raw_width = _as_int(blob.get("width"))
    raw_height = _as_int(blob.get("height"))
    orientation = _as_int(blob.get("orientation"), 1)

    people = [face["name"] for face in candidate["faces"]]
    keywords = list(candidate["keywords"])

    metadata: PhotoMetadata = {
        "keywords": keywords,
        "hierarchical_keywords": [
            f"{PERSON_KEYWORD_ROOT}|{name}" for name in dict.fromkeys(people)
        ],
        "written_at": written_at
        or datetime.datetime.now().isoformat(timespec="seconds"),
    }

    # Deliberately not written when the photo is not a favourite. PictoPy only
    # has a yes/no, so claiming the rating either way would let un-favouriting
    # erase a star rating the user set somewhere else.
    if candidate["is_favourite"]:
        metadata["rating"] = FAVOURITE_RATING

    regions: List[FaceRegion] = []
    for face in candidate["faces"]:
        placed = xmp_packet_orient_region(
            face["bbox"], raw_width, raw_height, orientation
        )
        if placed is None:
            continue
        center_x, center_y, width, height = placed
        regions.append(
            FaceRegion(
                name=face["name"],
                center_x=center_x,
                center_y=center_y,
                width=width,
                height=height,
            )
        )

    # Regions are meaningless without the frame they are measured against, so
    # both are written together or neither is.
    if regions and raw_width and raw_height:
        applied_width, applied_height = xmp_packet_applied_dimensions(
            raw_width, raw_height, orientation
        )
        metadata["regions"] = regions
        metadata["applied_width"] = applied_width
        metadata["applied_height"] = applied_height

    return metadata


def metadata_util_write_one(candidate: SyncCandidate) -> Optional[Dict[str, int]]:
    """
    Write one photo's packet into its file.

    Returns the file's new size and mtime, or None if it was left untouched.
    Every failure here is a skip rather than a raise: one unreadable photo must
    not stop the pass, and the file is always left exactly as it was.
    """
    path = candidate["path"]

    try:
        with open(path, "rb") as handle:
            original = handle.read()
    except OSError as e:
        logger.warning(f"Could not read {path} for metadata sync: {e}")
        return None

    try:
        existing = xmp_segments_read(original)
    except UnsupportedImageError as e:
        logger.warning(f"Cannot write metadata into {path}: {e}")
        return None

    try:
        packet = xmp_packet_build(
            metadata_util_build_packet_metadata(candidate), existing=existing
        )
    except UnreadablePacketError as e:
        # The photo carries a packet we cannot parse, so we cannot know what
        # replacing it would destroy. Leaving it alone is the point.
        logger.warning(f"Leaving {path} alone: {e}")
        return None

    try:
        updated = xmp_segments_write(original, packet)
    except (UnsupportedImageError, ValueError) as e:
        logger.warning(f"Cannot embed metadata in {path}: {e}")
        return None

    if updated == original:
        # Nothing changed, so there is no reason to rewrite the user's file.
        stats = os.stat(path)
        return {"file_size": stats.st_size, "file_mtime": int(stats.st_mtime)}

    if not self_write_util_replace(path, updated):
        return None

    stats = os.stat(path)
    return {"file_size": stats.st_size, "file_mtime": int(stats.st_mtime)}


def metadata_util_write_to_files_enabled() -> bool:
    """
    Whether the user has asked PictoPy to write into their originals.

    Read-only, like the memories curator: db_update_metadata rewrites the whole
    blob, so writing from here would clobber a concurrent settings save.
    """
    metadata = db_get_metadata() or {}
    stored = (metadata.get("user_preferences") or {}).get("metadata") or {}
    try:
        return MetadataPreferences.model_validate(stored).write_to_files
    except ValueError as e:
        logger.warning(f"Invalid metadata preferences, not writing to files: {e}")
        return False


def metadata_util_sync_pending(limit: int = 200) -> Dict[str, int]:
    """
    Write metadata into every photo whose file is behind the database.

    Photos that fail are left flagged and retried on the next pass, so a file
    that is merely locked or on a disconnected drive is not lost.
    """
    if not metadata_util_write_to_files_enabled():
        return {"considered": 0, "written": 0, "skipped": 0, "disabled": 1}

    candidates = db_get_images_pending_metadata_sync(limit)
    if not candidates:
        return {"considered": 0, "written": 0, "skipped": 0}

    written = []
    for candidate in candidates:
        result = metadata_util_write_one(candidate)
        if result is not None:
            written.append((candidate["id"], result["file_size"], result["file_mtime"]))

    db_mark_metadata_synced(written)

    summary = {
        "considered": len(candidates),
        "written": len(written),
        "skipped": len(candidates) - len(written),
    }
    logger.info(
        f"Metadata sync pass: {summary['written']} written, "
        f"{summary['skipped']} skipped of {summary['considered']}"
    )

    # The pass is capped so it cannot hold up the pipeline on a large library.
    # Saying so beats looking finished while thousands of photos still wait.
    remaining = db_count_images_pending_metadata_sync()
    if remaining:
        logger.info(f"{remaining} photo(s) still pending; run the pass again")

    return summary
