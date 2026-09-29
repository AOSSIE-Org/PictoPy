"""
Tests for image_util_is_valid_image(), image_util_generate_thumbnail(),
and image_util_load_cv2_image() accepting modern and mobile formats
(HEIC, HEIF, AVIF, WebP, BMP, TIFF/TIF, GIF) alongside jpg/jpeg/png.
"""

import os
import tempfile

import pytest
from PIL import Image

from app.utils.images import (
    image_util_is_valid_image,
    image_util_generate_thumbnail,
    image_util_load_cv2_image,
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
        (".heic", "HEIF"),
        (".heif", "HEIF"),
        (".avif", "AVIF"),
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


@pytest.mark.parametrize("extension,pil_format", [(".heic", "HEIF"), (".avif", "AVIF")])
def test_thumbnail_generation_for_heic_and_avif(temp_dir, extension, pil_format):
    img_path = os.path.join(temp_dir, f"source{extension}")
    thumb_path = os.path.join(temp_dir, f"thumb_{extension}.jpg")
    _make_image(img_path, pil_format)

    assert image_util_generate_thumbnail(img_path, thumb_path) is True
    assert os.path.exists(thumb_path) is True
    with Image.open(thumb_path) as thumb:
        assert thumb.format == "JPEG"


@pytest.mark.parametrize("extension,pil_format", [(".heic", "HEIF"), (".avif", "AVIF")])
def test_load_cv2_image_fallback_for_heic_and_avif(temp_dir, extension, pil_format):
    img_path = os.path.join(temp_dir, f"cv_source{extension}")
    _make_image(img_path, pil_format, size=(20, 30))

    cv_img = image_util_load_cv2_image(img_path)
    assert cv_img is not None
    assert cv_img.shape == (30, 20, 3)
