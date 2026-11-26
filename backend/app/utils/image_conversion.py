from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


_16BIT_GRAYSCALE_MODES = {"I;16", "I;16L", "I;16B"}


def image_util_normalize_16bit_grayscale(image: Image.Image) -> Image.Image:
    """Scale 16-bit grayscale pixels to matching 8-bit RGB values."""
    if image.mode in _16BIT_GRAYSCALE_MODES:
        pixels = np.asarray(image).astype(np.uint16, copy=False)
    elif image.mode == "I":
        pixels = np.asarray(image)
        if (
            pixels.size == 0
            or pixels.min() < 0
            or pixels.max() > np.iinfo(np.uint16).max
        ):
            return image
        pixels = pixels.astype(np.uint16)
    else:
        return image

    pixels_8bit = (pixels >> 8).astype(np.uint8)
    return Image.fromarray(pixels_8bit).convert("RGB")


def image_util_read_bgr(image_path: str) -> np.ndarray | None:
    """Read an OpenCV image, falling back for 16-bit TIFFs OpenCV cannot decode."""
    image = cv2.imread(image_path)
    if image is not None:
        return image

    try:
        with Image.open(image_path) as source:
            normalized = image_util_normalize_16bit_grayscale(source)
            if normalized is source:
                return None
            rgb = np.asarray(normalized)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except (OSError, ValueError):
        return None
