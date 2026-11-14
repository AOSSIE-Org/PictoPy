"""
image_util_generate_thumbnail() called Image.thumbnail() directly on the raw
pixel data, ignoring the EXIF Orientation tag (274) cameras write for portrait
photos. A photo stored landscape-side-up with Orientation=6 (needs a 90 CW
rotation to display upright) produced a sideways thumbnail instead of an
upright one.
"""

import os

from PIL import Image

from app.utils.images import image_util_generate_thumbnail


def _save_with_orientation(path: str, size: tuple[int, int], orientation: int) -> None:
    img = Image.new("RGB", size, "red")
    exif = img.getexif()
    exif[274] = orientation
    img.save(path, "JPEG", exif=exif)


def test_thumbnail_respects_exif_orientation(tmp_path) -> None:
    # Stored landscape (100x60) with Orientation=6 (90 CW needed) -- the
    # correct upright image is portrait (60x100), so the thumbnail's aspect
    # ratio should end up taller than it is wide.
    image_path = str(tmp_path / "portrait.jpg")
    thumbnail_path = str(tmp_path / "thumb.jpg")
    _save_with_orientation(image_path, (100, 60), orientation=6)

    assert image_util_generate_thumbnail(image_path, thumbnail_path) is True

    with Image.open(thumbnail_path) as thumb:
        width, height = thumb.size
    assert height > width


def test_thumbnail_unrotated_image_stays_landscape(tmp_path) -> None:
    # Orientation=1 (the default, "no rotation needed") must still produce a
    # landscape thumbnail -- this guards against overcorrecting.
    image_path = str(tmp_path / "landscape.jpg")
    thumbnail_path = str(tmp_path / "thumb.jpg")
    _save_with_orientation(image_path, (100, 60), orientation=1)

    assert image_util_generate_thumbnail(image_path, thumbnail_path) is True

    with Image.open(thumbnail_path) as thumb:
        width, height = thumb.size
    assert width > height
