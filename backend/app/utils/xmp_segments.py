"""
Putting an XMP packet into a JPEG or PNG without re-encoding the image.

Decoding a photo and saving it again would recompress it, losing a little more
of the user's original every time a tag changed. So the file is treated as a
marker or chunk stream and only the metadata block is spliced -- the compressed
image data is copied through byte for byte.

Bytes in, bytes out: nothing here opens a file.
"""

import struct
import zlib
from typing import List, Optional, Tuple

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

_JPEG_SOI = b"\xff\xd8"
_JPEG_APP1 = 0xE1
_JPEG_SOS = 0xDA
# Standalone markers carry no length field, so the walk cannot skip past them.
_JPEG_STANDALONE = {0x01, *range(0xD0, 0xD8)}

_XMP_NAMESPACE = b"http://ns.adobe.com/xap/1.0/\x00"

# A JPEG segment's length field is two bytes and includes itself, so this is the
# hard ceiling on one APP1 payload. Larger packets need ExtendedXMP, which we do
# not emit -- a photo that big keeps its metadata in the database instead.
_JPEG_MAX_SEGMENT = 0xFFFF - 2

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_XMP_KEYWORD = b"XML:com.adobe.xmp"
# iTXt: keyword \0 compression-flag compression-method \0 language \0 translated \0 text
_PNG_ITXT_PREFIX = _PNG_XMP_KEYWORD + b"\x00\x00\x00\x00\x00"


class UnsupportedImageError(Exception):
    """Raised for a container this module has no splice for."""


def _is_jpeg(data: bytes) -> bool:
    return data[:2] == _JPEG_SOI


def _is_png(data: bytes) -> bool:
    return data[:8] == _PNG_SIGNATURE


def _jpeg_segments(data: bytes) -> List[Tuple[int, int, int]]:
    """Walk the marker stream up to the scan, yielding (offset, marker, length)."""
    segments: List[Tuple[int, int, int]] = []
    offset = 2

    while offset + 3 < len(data):
        if data[offset] != 0xFF:
            break

        marker = data[offset + 1]
        if marker == _JPEG_SOS:
            break
        if marker in _JPEG_STANDALONE or marker == 0xFF:
            offset += 2
            continue

        length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
        if length < 2:
            break

        segments.append((offset, marker, length))
        offset += 2 + length

    return segments


def _jpeg_find_xmp(data: bytes) -> Optional[Tuple[int, int]]:
    """Locate an existing XMP APP1 as (offset, total segment size)."""
    for offset, marker, length in _jpeg_segments(data):
        if marker != _JPEG_APP1:
            continue
        payload = data[offset + 4 : offset + 2 + length]
        if payload.startswith(_XMP_NAMESPACE):
            return offset, 2 + length
    return None


def _jpeg_insert_offset(data: bytes) -> int:
    """
    Where a new XMP segment goes: after the leading APPn run.

    JFIF expects its APP0 first and readers look for Exif in the APP1 right
    after it, so a new segment goes at the end of that run rather than the front.
    """
    offset = 2
    for segment_offset, marker, length in _jpeg_segments(data):
        if 0xE0 <= marker <= 0xEF:
            offset = segment_offset + 2 + length
        else:
            break
    return offset


def _png_chunks(data: bytes) -> List[Tuple[int, bytes, int]]:
    """Walk the chunk stream, yielding (offset, type, data length)."""
    chunks: List[Tuple[int, bytes, int]] = []
    offset = len(_PNG_SIGNATURE)

    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunks.append((offset, chunk_type, length))
        if chunk_type == b"IEND":
            break
        offset += 12 + length

    return chunks


def _png_chunk(chunk_type: bytes, body: bytes) -> bytes:
    header = struct.pack(">I", len(body)) + chunk_type
    crc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
    return header + body + struct.pack(">I", crc)


def xmp_segments_read(data: bytes) -> Optional[bytes]:
    """Return the embedded XMP packet, or None if the file carries none."""
    if _is_jpeg(data):
        found = _jpeg_find_xmp(data)
        if not found:
            return None
        offset, size = found
        return data[offset + 4 + len(_XMP_NAMESPACE) : offset + size]

    if _is_png(data):
        for offset, chunk_type, length in _png_chunks(data):
            if chunk_type != b"iTXt":
                continue
            body = data[offset + 8 : offset + 8 + length]
            if body.startswith(_PNG_XMP_KEYWORD + b"\x00"):
                return body[len(_PNG_ITXT_PREFIX) :]
        return None

    raise UnsupportedImageError("Not a JPEG or PNG")


def xmp_segments_write(data: bytes, packet: bytes) -> bytes:
    """
    Return the file with `packet` embedded, replacing any packet already there.

    Every byte outside the metadata block is copied through untouched, so the
    image itself is bit-identical to what went in.
    """
    if _is_jpeg(data):
        payload = _XMP_NAMESPACE + packet
        if len(payload) > _JPEG_MAX_SEGMENT:
            raise ValueError(
                f"XMP packet needs {len(payload)} bytes, over the "
                f"{_JPEG_MAX_SEGMENT}-byte JPEG segment limit"
            )

        segment = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload

        found = _jpeg_find_xmp(data)
        if found:
            offset, size = found
            return data[:offset] + segment + data[offset + size :]

        offset = _jpeg_insert_offset(data)
        return data[:offset] + segment + data[offset:]

    if _is_png(data):
        chunk = _png_chunk(b"iTXt", _PNG_ITXT_PREFIX + packet)

        for offset, chunk_type, length in _png_chunks(data):
            if chunk_type != b"iTXt":
                continue
            body = data[offset + 8 : offset + 8 + length]
            if body.startswith(_PNG_XMP_KEYWORD + b"\x00"):
                return data[:offset] + chunk + data[offset + 12 + length :]

        # A new chunk goes after IHDR, which must stay first.
        for offset, chunk_type, length in _png_chunks(data):
            if chunk_type == b"IHDR":
                end = offset + 12 + length
                return data[:end] + chunk + data[end:]

        raise UnsupportedImageError("PNG has no IHDR chunk")

    raise UnsupportedImageError("Not a JPEG or PNG")
