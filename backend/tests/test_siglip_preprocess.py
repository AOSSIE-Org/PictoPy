"""siglip_util_preprocess_image must feed SigLIP the photo the way it is displayed."""

from pathlib import Path
from typing import Optional

import numpy as np
import pytest
from PIL import Image

from app.utils.SigLIP import siglip_util_preprocess_image

RESOLUTION = 32
EXIF_ORIENTATION = 0x0112


def _save_red_left_blue_right(path: Path, orientation: Optional[int] = None) -> None:
    # Landscape pixels: red left half, blue right half.
    pixels = np.zeros((40, 80, 3), dtype=np.uint8)
    pixels[:, :40] = (255, 0, 0)
    pixels[:, 40:] = (0, 0, 255)
    img = Image.fromarray(pixels)
    exif = img.getexif()
    if orientation is not None:
        exif[EXIF_ORIENTATION] = orientation
    img.save(path, "JPEG", exif=exif, quality=95)


def _red_side(chw: np.ndarray) -> str:
    # Values are normalized to [-1, 1]; red channel > 0 means red.
    red = chw[0] > 0
    half = RESOLUTION // 2
    sides = {
        "top": red[:half].mean(),
        "bottom": red[half:].mean(),
        "left": red[:, :half].mean(),
        "right": red[:, half:].mean(),
    }
    return max(sides, key=sides.get)


@pytest.mark.parametrize(
    "orientation,expected_red_side",
    [
        (None, "left"),  # no tag: shown as stored
        (1, "left"),  # normal
        (3, "right"),  # rotate 180
        (6, "top"),  # rotate 90 CW, typical phone portrait
        (8, "bottom"),  # rotate 90 CCW
    ],
)
def test_preprocess_applies_exif_orientation(tmp_path, orientation, expected_red_side):
    path = tmp_path / "photo.jpg"
    _save_red_left_blue_right(path, orientation)

    result = siglip_util_preprocess_image(str(path), RESOLUTION)

    assert result is not None
    assert result.shape == (3, RESOLUTION, RESOLUTION)
    assert result.dtype == np.float32
    assert _red_side(result) == expected_red_side


def test_preprocess_returns_none_for_unreadable_file(tmp_path):
    path = tmp_path / "broken.jpg"
    path.write_bytes(b"not an image")

    assert siglip_util_preprocess_image(str(path), RESOLUTION) is None
