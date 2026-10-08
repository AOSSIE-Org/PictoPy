"""
Read capture date and GPS out of Google Takeout sidecar JSON files.

A Google Photos export strips EXIF from a meaningful slice of its own
images and parks the real values in a sibling JSON file instead. Without
this the only date left is the file's mtime, which is when the export was
copied, not when the photo was taken.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, Iterator, Optional, Tuple

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# Google has shipped several sidecar spellings over the years, and truncates
# long ones. Ordered most specific first.
SIDECAR_SUFFIXES = (".supplemental-metadata.json", ".json")

# Album-level files sit beside the photos and match no image; skip by key.
ALBUM_METADATA_KEYS = frozenset({"entries", "albumData"})


# The last directory listing, reused across its images. A sidecar lookup runs
# for every photo missing EXIF GPS, so scanning per photo made an N-file folder
# cost N scans of N entries. The stamp is read as one tuple, so a concurrent
# write can only cost a rescan, never a wrong answer.
_LISTING_CACHE: Tuple[Optional[str], float, Tuple[str, ...]] = (None, 0.0, ())


def _sidecar_names(directory: str) -> Tuple[str, ...]:
    """JSON filenames in a directory, re-read only once the directory changes."""
    global _LISTING_CACHE
    try:
        stamp = os.stat(directory).st_mtime
    except OSError:
        return ()

    cached_directory, cached_stamp, names = _LISTING_CACHE
    if cached_directory == directory and cached_stamp == stamp:
        return names

    try:
        with os.scandir(directory) as entries:
            names = tuple(sorted(e.name for e in entries if e.name.endswith(".json")))
    except OSError:
        names = ()

    _LISTING_CACHE = (directory, stamp, names)
    return names


def _candidate_paths(image_path: str) -> Iterator[str]:
    """
    Sidecar paths to try for an image, most likely first.

    A generator on purpose: the exact spellings cost a stat each, and the
    directory listing behind the rarer ones is only touched if none of them
    produced a usable sidecar.
    """
    seen = set()
    for suffix in SIDECAR_SUFFIXES:
        candidate = image_path + suffix
        if os.path.exists(candidate):
            seen.add(candidate)
            yield candidate

    # Catches the duplicate-index spelling (`.supplemental-metadata(1).json`)
    # and any variant Takeout has used that is not listed above.
    directory, basename = os.path.split(image_path)
    prefix = basename + "."
    for name in _sidecar_names(directory or "."):
        if not name.startswith(prefix):
            continue
        # Rebuilt off image_path rather than joined, so the separator matches
        # the caller's and the paths above dedupe exactly.
        candidate = image_path + name[len(basename) :]
        if candidate not in seen:
            yield candidate


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
