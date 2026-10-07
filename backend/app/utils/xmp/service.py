from enum import Enum
from typing import Optional

from app.logging.setup_logging import get_logger

from .codec import NewerSchemaError, PictoPyXmpCodec, XmpCodec
from .containers import get_container
from .containers.base import TransformedStream
from .containers.png import PngFormatError
from .schema import PictoPyMetadata

logger = get_logger(__name__)

_codec: XmpCodec = PictoPyXmpCodec()


class WriteOutcome(str, Enum):
    WRITTEN = "written"
    # The image already holds exactly this data; the file was not touched.
    UNCHANGED = "unchanged"
    UNSUPPORTED = "unsupported"
    # A newer PictoPy wrote this image; leave its data alone.
    NEWER_SCHEMA = "newer_schema"


def is_xmp_supported(path: str) -> bool:
    return get_container(path) is not None


def write_image_metadata(
    path: str, metadata: PictoPyMetadata, codec: XmpCodec = _codec
) -> WriteOutcome:
    """Embed `metadata` in the image unless it already holds the same data.

    Other tools' XMP is kept. Raises OSError/ValueError when the file cannot be
    read or written; callers decide how a failure is reported.
    """
    container = get_container(path)
    if container is None:
        return WriteOutcome.UNSUPPORTED

    existing = container.read_xmp(path)
    if existing:
        header = codec.read_header(existing)
        if header is not None and header.digest == codec.digest(metadata):
            return WriteOutcome.UNCHANGED

    try:
        packet = codec.encode(metadata, existing=existing)
    except NewerSchemaError as e:
        logger.info(f"Not overwriting newer PictoPy metadata in {path}: {e}")
        return WriteOutcome.NEWER_SCHEMA
    container.write_xmp(path, packet)
    return WriteOutcome.WRITTEN


def _strip_or_drop(packet: bytes, codec: XmpCodec) -> Optional[bytes]:
    try:
        return codec.strip(packet)
    except ValueError as e:
        # Fail closed: a packet we cannot clean may still hold face data.
        logger.debug(f"Dropping XMP packet that could not be stripped: {e}")
        return None


def open_without_pictopy(
    path: str, codec: XmpCodec = _codec
) -> Optional[TransformedStream]:
    """Stream the image with PictoPy's data removed; the file is not modified.

    Returns None for formats without a container, which carry no PictoPy data
    and can be served as they are.
    """
    container = get_container(path)
    if container is None:
        return None
    return container.stream_with_xmp(path, lambda p: _strip_or_drop(p, codec))


def read_image_metadata(
    path: str, codec: XmpCodec = _codec
) -> Optional[PictoPyMetadata]:
    """PictoPy data stored in the image, or None if absent or unreadable."""
    container = get_container(path)
    if container is None:
        return None
    try:
        packet = container.read_xmp(path)
    except (OSError, PngFormatError) as e:
        logger.warning(f"Could not read XMP from {path}: {e}")
        return None
    return codec.decode(packet) if packet else None
