"""
Unit tests for face quality assessment module.

Tests the face quality functions including sharpness, brightness, 
size assessment, and filtering functionality.
"""

import pytest
import numpy as np

from app.utils.face_quality import (
    assess_face_sharpness,
    assess_face_brightness,
    assess_face_size,
    calculate_face_quality,
    should_include_face,
    filter_quality_faces,
)


class TestAssessFaceSharpness:
    """Tests for assess_face_sharpness function."""

    def test_sharp_image_high_score(self):
        """Test that a sharp, high-contrast image gets high score."""
        # Create checkerboard pattern (very sharp)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[::2, ::2] = 255

        score = assess_face_sharpness(img)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high

    def test_blurry_image_low_score(self):
        """Test that a blurry, uniform image gets low score."""
        # Create uniform gray image (very blurry)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        score = assess_face_sharpness(img)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score < 0.3  # Should be low

    def test_grayscale_input(self):
        """Test that grayscale images are handled correctly."""
        gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        score = assess_face_sharpness(gray)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestAssessFaceBrightness:
    """Tests for assess_face_brightness function."""

    def test_optimal_brightness_high_score(self):
        """Test that optimal brightness (128) gets high score."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        score = assess_face_brightness(img)

        assert isinstance(score, float)
        assert score > 0.9  # Near perfect

    def test_dark_image_low_score(self):
        """Test that very dark image gets low score."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 20

        score = assess_face_brightness(img)

        assert isinstance(score, float)
        assert score < 0.3  # Should be low

    def test_overexposed_low_score(self):
        """Test that overexposed image gets low score."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 240

        score = assess_face_brightness(img)

        assert isinstance(score, float)
        assert score < 0.3  # Should be low


class TestAssessFaceSize:
    """Tests for assess_face_size function."""

    def test_large_face_high_score(self):
        """Test that large face gets high score."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)

        score = assess_face_size(img, target_size=160)

        assert score == 1.0  # Larger than target = 1.0

    def test_target_size_perfect_score(self):
        """Test that exact target size gets perfect score."""
        img = np.zeros((160, 160, 3), dtype=np.uint8)

        score = assess_face_size(img, target_size=160)

        assert score == 1.0

    def test_small_face_proportional_score(self):
        """Test that small face gets proportionally lower score."""
        img = np.zeros((80, 80, 3), dtype=np.uint8)

        score = assess_face_size(img, target_size=160)

        assert score == 0.5  # 80/160 = 0.5

    def test_rectangular_uses_min_dimension(self):
        """Test that rectangular images use minimum dimension."""
        img = np.zeros((160, 80, 3), dtype=np.uint8)

        score = assess_face_size(img, target_size=160)

        assert score == 0.5  # min(160, 80) / 160 = 0.5


class TestCalculateFaceQuality:
    """Tests for calculate_face_quality function."""

    def test_returns_dict_with_all_keys(self):
        """Test that function returns dict with all required keys."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = calculate_face_quality(img)

        assert isinstance(result, dict)
        assert "quality" in result
        assert "sharpness" in result
        assert "brightness" in result
        assert "size" in result

    def test_all_scores_in_valid_range(self):
        """Test that all scores are between 0 and 1."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = calculate_face_quality(img)

        for key, value in result.items():
            assert 0.0 <= value <= 1.0, f"{key} out of range: {value}"

    def test_custom_weights(self):
        """Test with custom weights."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = calculate_face_quality(
            img, sharpness_weight=0.5, brightness_weight=0.25, size_weight=0.25
        )

        assert isinstance(result, dict)

    def test_invalid_weights_raises_error(self):
        """Test that weights not summing to 1.0 raises error."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with pytest.raises(ValueError):
            calculate_face_quality(
                img,
                sharpness_weight=0.5,
                brightness_weight=0.5,
                size_weight=0.5,  # Sum = 1.5
            )

    def test_high_quality_face(self):
        """Test that high-quality face gets high overall score."""
        # Create sharp, well-lit, large image
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[::2, ::2] = 180  # Checkerboard near optimal brightness
        img[1::2, 1::2] = 80

        result = calculate_face_quality(img)

        assert result["quality"] > 0.5


class TestShouldIncludeFace:
    """Tests for should_include_face function."""

    def test_above_threshold_included(self):
        """Test that score above threshold returns True."""
        assert should_include_face(0.5, min_threshold=0.4) is True

    def test_below_threshold_excluded(self):
        """Test that score below threshold returns False."""
        assert should_include_face(0.3, min_threshold=0.4) is False

    def test_exact_threshold_included(self):
        """Test that score exactly at threshold returns True."""
        assert should_include_face(0.4, min_threshold=0.4) is True

    def test_custom_threshold(self):
        """Test with custom threshold."""
        assert should_include_face(0.7, min_threshold=0.8) is False
        assert should_include_face(0.9, min_threshold=0.8) is True


class TestFilterQualityFaces:
    """Tests for filter_quality_faces function."""

    def test_filters_low_quality(self):
        """Test that low quality faces are filtered out."""
        faces = [
            {"face_id": 1, "quality": 0.8},
            {"face_id": 2, "quality": 0.3},
            {"face_id": 3, "quality": 0.6},
        ]

        result = filter_quality_faces(faces, min_quality=0.4)

        assert len(result) == 2
        assert result[0]["face_id"] == 1
        assert result[1]["face_id"] == 3

    def test_empty_list(self):
        """Test with empty list."""
        result = filter_quality_faces([], min_quality=0.4)
        assert result == []

    def test_all_pass(self):
        """Test when all faces pass quality check."""
        faces = [
            {"face_id": 1, "quality": 0.8},
            {"face_id": 2, "quality": 0.9},
        ]

        result = filter_quality_faces(faces, min_quality=0.4)

        assert len(result) == 2

    def test_all_fail(self):
        """Test when all faces fail quality check."""
        faces = [
            {"face_id": 1, "quality": 0.1},
            {"face_id": 2, "quality": 0.2},
        ]

        result = filter_quality_faces(faces, min_quality=0.4)

        assert len(result) == 0

    def test_missing_quality_key_defaults_to_zero(self):
        """Test that faces without quality key are treated as 0."""
        faces = [
            {"face_id": 1, "quality": 0.8},
            {"face_id": 2},  # No quality key
        ]

        result = filter_quality_faces(faces, min_quality=0.4)

        assert len(result) == 1
        assert result[0]["face_id"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
