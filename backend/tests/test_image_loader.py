import cv2
import numpy as np
import pytest
from PIL import Image

from app.utils.image_loader import load_image_bgr


@pytest.fixture
def pixels() -> np.ndarray:
    """Distinct channel values, so a BGR/RGB mix-up is caught."""
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 10, 120, 240  # B, G, R
    return img


def test_loads_png_as_bgr(tmp_path, pixels):
    path = tmp_path / "photo.png"
    cv2.imwrite(str(path), pixels)

    img = load_image_bgr(str(path))

    assert img is not None
    assert np.array_equal(img, pixels)


def test_loads_non_ascii_path(tmp_path, pixels):
    folder = tmp_path / "फोटो"
    folder.mkdir()
    path = folder / "चित्र é.png"
    ok, buf = cv2.imencode(".png", pixels)
    assert ok
    buf.tofile(str(path))

    img = load_image_bgr(str(path))

    assert img is not None
    assert np.array_equal(img, pixels)


def test_falls_back_to_pillow_for_gif(tmp_path, pixels):
    path = tmp_path / "anim.gif"
    Image.fromarray(pixels[..., ::-1]).save(path)  # Pillow expects RGB

    img = load_image_bgr(str(path))

    assert img is not None
    assert img.shape == (8, 8, 3)
    # GIF is palette based, so allow a small quantisation error
    assert np.abs(img.astype(int) - pixels.astype(int)).max() <= 8


def test_returns_none_for_missing_file(tmp_path):
    assert load_image_bgr(str(tmp_path / "missing.png")) is None


def test_returns_none_for_empty_file(tmp_path):
    path = tmp_path / "empty.jpg"
    path.write_bytes(b"")

    assert load_image_bgr(str(path)) is None


def test_returns_none_for_corrupt_file(tmp_path):
    path = tmp_path / "corrupt.jpg"
    path.write_bytes(b"this is not an image")

    assert load_image_bgr(str(path)) is None
