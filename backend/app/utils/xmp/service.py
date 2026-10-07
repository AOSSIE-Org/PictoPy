from typing import Optional

from app.logging.setup_logging import get_logger

from .codec import PictoPyXmpCodec, XmpCodec
from .containers import get_container
from .schema import PictoPyMetadata

logger = get_logger(__name__)

_codec: XmpCodec = PictoPyXmpCodec()


def is_xmp_supported(path: str) -> bool:
    return get_container(path) is not None


def write_image_metadata(
    path: str, metadata: PictoPyMetadata, codec: XmpCodec = _codec
) -> bool:
    """Embed `metadata` in the image, keeping any XMP other tools put there.

    Returns False for formats without a container. The write changes the file's
    size and mtime, which the folder rescan uses to detect edits.
    """
    container = get_container(path)
    if container is None:
        return False
    packet = codec.encode(metadata, existing=container.read_xmp(path))
    container.write_xmp(path, packet)
    return True


def read_image_metadata(
    path: str, codec: XmpCodec = _codec
) -> Optional[PictoPyMetadata]:
    """PictoPy data stored in the image, or None if absent or unreadable."""
    container = get_container(path)
    if container is None:
        return None
    try:
        packet = container.read_xmp(path)
    except (OSError, ValueError) as e:
        logger.warning(f"Could not read XMP from {path}: {e}")
        return None
    return codec.decode(packet) if packet else None
