"""
Tests for image_util_is_valid_image() accepting the additional formats
(WebP, BMP, TIFF/TIF, GIF) added alongside the existing jpg/jpeg/png support,
and image_util_generate_thumbnail() handling various image modes.
"""

import os
import tempfile
from typing import Any, Dict

import pytest
from PIL import Image

from app.utils.images import (
    image_util_generate_thumbnail,
    image_util_is_valid_image,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


def _make_image(path: str, fmt: str, mode: str = "RGB", size=(10, 10)):
    img = Image.new(mode, size, color="red")
    img.save(path, fmt)


@pytest.mark.parametrize(
    "extension,pil_format",
    [
        (".webp", "WEBP"),
        (".bmp", "BMP"),
        (".tiff", "TIFF"),
        (".tif", "TIFF"),
        (".gif", "GIF"),
        (".jpg", "JPEG"),
        (".jpeg", "JPEG"),
        (".png", "PNG"),
    ],
)
def test_valid_image_formats_are_accepted(temp_dir, extension, pil_format):
    path = os.path.join(temp_dir, f"sample{extension}")
    _make_image(path, pil_format)

    assert image_util_is_valid_image(path) is True


def test_unsupported_extension_is_rejected(temp_dir):
    path = os.path.join(temp_dir, "notes.txt")
    with open(path, "w") as f:
        f.write("not an image")

    assert image_util_is_valid_image(path) is False


def test_corrupt_file_with_valid_extension_is_rejected(temp_dir):
    path = os.path.join(temp_dir, "broken.png")
    with open(path, "wb") as f:
        f.write(b"not a real png")

    assert image_util_is_valid_image(path) is False


@pytest.mark.parametrize(
    "mode,fmt,save_kwargs",
    [
        ("RGB", "JPEG", {}),
        ("RGBA", "PNG", {}),
        ("LA", "PNG", {}),
        ("L", "PNG", {}),
        ("1", "PNG", {}),
        ("CMYK", "JPEG", {}),
        ("P", "PNG", {}),
        ("P", "PNG", {"transparency": 0}),
    ],
)
def test_generate_thumbnail_handles_various_modes(
    temp_dir: str, mode: str, fmt: str, save_kwargs: Dict[str, Any]
) -> None:
    src_path = os.path.join(temp_dir, f"source_{mode}.{fmt.lower()}")
    thumb_path = os.path.join(temp_dir, f"thumb_{mode}.jpg")

    if mode == "P":
        base = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        img = base.convert("P", palette=Image.Palette.ADAPTIVE)
    elif mode == "1":
        img = Image.new("1", (100, 100), 1)
    elif mode == "L":
        img = Image.new("L", (100, 100), 128)
    elif mode == "LA":
        img = Image.new("LA", (100, 100), (128, 200))
    elif mode == "RGBA":
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    elif mode == "CMYK":
        img = Image.new("CMYK", (100, 100), (0, 255, 255, 0))
    else:
        img = Image.new("RGB", (100, 100), (255, 0, 0))

    img.save(src_path, fmt, **save_kwargs)

    success = image_util_generate_thumbnail(src_path, thumb_path, size=(50, 50))
    assert success is True
    assert os.path.exists(thumb_path)

    with Image.open(thumb_path) as thumb:
        assert thumb.format == "JPEG"
        assert thumb.mode == "RGB"
