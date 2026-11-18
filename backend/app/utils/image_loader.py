import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps, UnidentifiedImageError

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def load_image_bgr(image_path: str) -> NDArray[np.uint8] | None:
    """Read an image file as a BGR array, or None if it cannot be decoded.

    cv2.imread returns None for non-ASCII paths on Windows and has no GIF
    decoder, so the bytes are read here and decoded from memory instead.
    """
    try:
        data: NDArray[np.uint8] = np.fromfile(image_path, dtype=np.uint8)
    except OSError as e:
        logger.error("Failed to read image file %s: %s", image_path, e)
        return None

    # imdecode raises on an empty buffer instead of returning None
    img = cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None
    if img is not None:
        return img

    # OpenCV cannot decode every format PictoPy accepts (e.g. GIF), Pillow can.
    # exif_transpose matches cv2, which applies the EXIF orientation itself.
    try:
        with Image.open(image_path) as pil_img:
            rgb = np.asarray(
                ImageOps.exif_transpose(pil_img).convert("RGB"), dtype=np.uint8
            )
    except (
        OSError,
        UnidentifiedImageError,
        ValueError,
        SyntaxError,  # Pillow's PNG decoder raises this for broken chunks
        Image.DecompressionBombError,
    ) as e:
        logger.error("Failed to decode image %s: %s", image_path, e)
        return None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
