"""
Tests for image_util_is_valid_image() accepting the additional formats
(WebP, BMP, TIFF, GIF) added alongside the existing jpg/jpeg/png support.
"""

import os
import tempfile

import pytest
from PIL import Image

from app.utils.images import image_util_is_valid_image


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
