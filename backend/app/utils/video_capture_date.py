"""
Read capture timestamps out of MP4/MOV containers.

OpenCV exposes no creation date, so videos had nothing to fall back on but
the file's mtime — which on a copied library is import day. Both timestamps
an ISO base media file can carry are read here, without ffprobe: PictoPy
ships through PyInstaller and cannot assume ffmpeg exists on the machine.
"""

from __future__ import annotations

import datetime
import struct
from typing import BinaryIO, Iterator, Optional, Tuple

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# Box time bases and the key holding a real, offset-aware capture time.
EPOCH_1904 = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)
QUICKTIME_CREATION_KEY = b"com.apple.quicktime.creationdate"

# A container can carry 0, or a clock that was never set. Anything outside
# this range is noise, not a capture date.
EARLIEST_PLAUSIBLE = datetime.datetime(1990, 1, 1)
FUTURE_TOLERANCE = datetime.timedelta(days=2)

# Guards against a malformed keys table allocating unbounded memory.
MAX_METADATA_KEYS = 512


def _boxes(handle: BinaryIO, end: int) -> Iterator[Tuple[bytes, int, int]]:
    """Walk sibling boxes, yielding (type, payload_start, box_end)."""
    while handle.tell() < end:
        start = handle.tell()
        header = handle.read(8)
        if len(header) < 8:
            return
        size, kind = struct.unpack(">I4s", header)
        header_size = 8
        if size == 1:
            extended = handle.read(8)
            if len(extended) < 8:
                return
            size = struct.unpack(">Q", extended)[0]
            header_size = 16
        elif size == 0:
            size = end - start
        if size < header_size or start + size > end:
            return
        yield kind, start + header_size, start + size
        handle.seek(start + size)


def _find(
    handle: BinaryIO, want: bytes, start: int, end: int
) -> Optional[Tuple[int, int]]:
    handle.seek(start)
    for kind, payload_start, box_end in _boxes(handle, end):
        if kind == want:
            return payload_start, box_end
    return None


def _meta_children_start(handle: BinaryIO, start: int) -> int:
    """
    QuickTime writes `meta` as a plain container; ISO adds version and flags.

    Sniffed rather than assumed: guessing wrong finds no children at all, and
    the files that carry the good timestamp are the QuickTime-style ones.
    """
    handle.seek(start)
    head = handle.read(12)
    if head[4:8] == b"hdlr":
        return start
    if head[8:12] == b"hdlr":
        return start + 4
    return start


def _plausible(value: datetime.datetime) -> Optional[datetime.datetime]:
    horizon = datetime.datetime.now() + FUTURE_TOLERANCE
    if EARLIEST_PLAUSIBLE <= value <= horizon:
        return value
    return None


def _parse_iso(value: str) -> Optional[datetime.datetime]:
    """
    Parse the QuickTime creation date, which carries a UTC offset.

    The offset is what makes this the best source available: it yields the
    wall-clock time where the video was shot, exactly as EXIF does for a
    photo. Everything else is an absolute instant needing a guessed zone.
    """
    text = value.strip().rstrip("\x00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=None, microsecond=0)
    return None


def _quicktime_creation_date(handle: BinaryIO, meta: Tuple[int, int]) -> Optional[str]:
    """Read moov/meta the way the format actually stores it: keys then ilst."""
    children = _meta_children_start(handle, meta[0])
    keys = _find(handle, b"keys", children, meta[1])
    ilst = _find(handle, b"ilst", children, meta[1])
    if not keys or not ilst:
        return None

    handle.seek(keys[0] + 4)  # version and flags
    count = struct.unpack(">I", handle.read(4))[0]
    index = None
    for position in range(min(count, MAX_METADATA_KEYS)):
        size_bytes = handle.read(4)
        if len(size_bytes) < 4:
            return None
        size = struct.unpack(">I", size_bytes)[0]
        handle.read(4)  # namespace
        name = handle.read(max(size - 8, 0))
        if name == QUICKTIME_CREATION_KEY:
            index = position + 1  # ilst entries are 1-based key indices
            break
    if index is None:
        return None

    handle.seek(ilst[0])
    for kind, payload_start, box_end in _boxes(handle, ilst[1]):
        if int.from_bytes(kind, "big") != index:
            continue
        data = _find(handle, b"data", payload_start, box_end)
        if not data:
            return None
        handle.seek(data[0] + 8)  # type indicator and locale
        raw = handle.read(data[1] - data[0] - 8)
        parsed = _parse_iso(raw.decode("ascii", "ignore"))
        return parsed.isoformat() if parsed and _plausible(parsed) else None
    return None


def _mvhd_creation_time(handle: BinaryIO, moov: Tuple[int, int]) -> Optional[str]:
    """
    Read moov/mvhd, which counts seconds from 1904 in UTC.

    Converted to local time, since that is what every other capture date in
    the database means. The machine's current zone is the only one available,
    so a video shot abroad lands at the hour it would have been here — still
    far closer than the import date it would otherwise carry.
    """
    mvhd = _find(handle, b"mvhd", *moov)
    if not mvhd:
        return None

    handle.seek(mvhd[0])
    version_byte = handle.read(1)
    if not version_byte:
        return None
    handle.read(3)  # flags

    width = 8 if version_byte[0] == 1 else 4
    raw = handle.read(width)
    if len(raw) < width:
        return None
    seconds = struct.unpack(">Q" if width == 8 else ">I", raw)[0]
    if not seconds:
        return None

    try:
        utc = EPOCH_1904 + datetime.timedelta(seconds=seconds)
        local = utc.astimezone().replace(tzinfo=None, microsecond=0)
    except (OverflowError, OSError, ValueError):
        return None
    return local.isoformat() if _plausible(local) else None


def video_capture_date_candidates(
    video_path: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (recorded_at, file_created_at) as local ISO strings.

    `recorded_at` is the QuickTime capture time and is authoritative — it
    carries its own UTC offset. `file_created_at` comes from the movie header
    and is weaker evidence: it is when *this file* was written, so a re-encode
    or a trim overwrites it. Both are None when the container says nothing.
    """
    try:
        with open(video_path, "rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            moov = _find(handle, b"moov", 0, size)
            if not moov:
                return None, None

            file_created = _mvhd_creation_time(handle, moov)
            meta = _find(handle, b"meta", *moov)
            recorded = _quicktime_creation_date(handle, meta) if meta else None
            return recorded, file_created
    except (OSError, ValueError, struct.error):
        logger.debug("Container date lookup failed for %s", video_path, exc_info=True)
        return None, None
