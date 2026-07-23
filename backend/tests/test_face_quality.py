import numpy as np

from app.utils.face_quality import face_passes_quality_gate

# ##############################
# Helpers
# ##############################


def sharp_gray(size=50):
    """A deterministic high-variance (sharp) grayscale image."""
    img = np.zeros((size, size), dtype=np.uint8)
    img[::2] = 255  # alternating rows -> large Laplacian variance
    return img


# ##############################
# Quality gate
# ##############################


class TestFaceQualityGate:
    def test_passes_all_gates(self):
        crop = np.stack([sharp_gray()] * 3, axis=-1)  # 3-channel colour crop
        assert (
            face_passes_quality_gate(
                crop,
                bbox=(0, 0, 50, 50),
                conf_score=0.9,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=100,
            )
            is True
        )

    def test_rejects_low_confidence(self):
        crop = np.stack([sharp_gray()] * 3, axis=-1)
        assert (
            face_passes_quality_gate(
                crop,
                bbox=(0, 0, 50, 50),
                conf_score=0.1,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=100,
            )
            is False
        )

    def test_rejects_small_face(self):
        crop = np.stack([sharp_gray()] * 3, axis=-1)
        assert (
            face_passes_quality_gate(
                crop,
                bbox=(0, 0, 50, 50),
                conf_score=0.9,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=10000,  # area 2500 < threshold
            )
            is False
        )

    def test_rejects_empty_crop(self):
        assert (
            face_passes_quality_gate(
                np.empty((0, 0, 3), dtype=np.uint8),
                bbox=(0, 0, 50, 50),
                conf_score=0.9,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=100,
            )
            is False
        )

    def test_accepts_grayscale_crop(self):
        # A 2-D crop skips the BGR2GRAY conversion branch
        assert (
            face_passes_quality_gate(
                sharp_gray(),
                bbox=(0, 0, 50, 50),
                conf_score=0.9,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=100,
            )
            is True
        )

    def test_rejects_blurry_crop(self):
        flat = np.full((50, 50, 3), 127, dtype=np.uint8)  # zero-variance -> blurry
        assert (
            face_passes_quality_gate(
                flat,
                bbox=(0, 0, 50, 50),
                conf_score=0.9,
                conf_threshold=0.5,
                blur_threshold=10.0,
                min_face_size=100,
            )
            is False
        )
