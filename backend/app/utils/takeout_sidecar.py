"""
Read capture date and GPS out of Google Takeout sidecar JSON files.

A Google Photos export strips EXIF from a meaningful slice of its own
images and parks the real values in a sibling JSON file instead. Without
this the only date left is the file's mtime, which is when the export was
copied, not when the photo was taken.
"""

from __future__ import annotations

import datetime
import glob
import json
from typing import Any, Dict, Optional, Tuple

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# Google has shipped several sidecar spellings over the years, and truncates
# long ones. Ordered most specific first.
SIDECAR_SUFFIXES = (".supplemental-metadata.json", ".json")

# Album-level files sit beside the photos and match no image; skip by key.
ALBUM_METADATA_KEYS = frozenset({"entries", "albumData"})


def _candidate_paths(image_path: str) -> list:
    """Sidecar paths to try for an image, most likely first."""
    candidates = [image_path + suffix for suffix in SIDECAR_SUFFIXES]

    # Catches the duplicate-index spelling (`.supplemental-metadata(1).json`)
    # and any variant Takeout has used that is not listed above.
    candidates += sorted(glob.glob(glob.escape(image_path) + ".*.json"))

    seen = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


def _load(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict) or ALBUM_METADATA_KEYS & payload.keys():
        return None
    return payload


def _read_timestamp(payload: Dict[str, Any]) -> Optional[str]:
    """`photoTakenTime` is the shutter time; `creationTime` is the upload."""
    for key in ("photoTakenTime", "creationTime"):
        block = payload.get(key)
        if not isinstance(block, dict):
            continue
        raw = block.get("timestamp")
        if raw in (None, "", 0, "0"):
            continue
        try:
            epoch = int(raw)
        except (TypeError, ValueError):
            continue
        try:
            return datetime.datetime.fromtimestamp(epoch).strftime("%Y:%m:%d %H:%M:%S")
        except (OSError, OverflowError, ValueError):
            continue
    return None


def _read_coordinates(
    payload: Dict[str, Any],
) -> Tuple[Optional[float], Optional[float]]:
    """`geoData` is Google's resolved location; `geoDataExif` the original."""
    for key in ("geoData", "geoDataExif"):
        block = payload.get(key)
        if not isinstance(block, dict):
            continue
        try:
            latitude = float(block.get("latitude"))
            longitude = float(block.get("longitude"))
        except (TypeError, ValueError):
            continue
        # Takeout writes 0/0 for "no location", not null.
        if latitude == 0.0 and longitude == 0.0:
            continue
        if -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0:
            return latitude, longitude
    return None, None


def takeout_sidecar_read(
    image_path: str,
) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Return (capture_datetime, latitude, longitude) from an image's sidecar.

    The datetime is EXIF-formatted so callers can parse it exactly as they
    parse a real EXIF value. Any field with nothing usable comes back None.
    """
    try:
        for path in _candidate_paths(image_path):
            payload = _load(path)
            if payload is None:
                continue
            captured_at = _read_timestamp(payload)
            latitude, longitude = _read_coordinates(payload)
            if captured_at or latitude is not None:
                return captured_at, latitude, longitude
    except Exception:
        logger.debug("Sidecar lookup failed for %s", image_path, exc_info=True)

    return None, None, None
