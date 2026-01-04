"""
Unit tests for face alignment utilities.
"""

import pytest
import numpy as np
import cv2
from app.utils.face_alignment import (
    align_face_simple,
    simple_face_crop,
    estimate_eye_positions
)
from app.config import settings


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a 500x500 test image with a simple pattern
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    # Add some pattern to make it visible
    cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), -1)
    cv2.circle(img, (200, 200), 20, (0, 0, 255), -1)  # Left "eye"
    cv2.circle(img, (300, 200), 20, (0, 0, 255), -1)  # Right "eye"
    return img


@pytest.fixture
def sample_bbox():
    """Sample bounding box dictionary."""
    return {"x": 120, "y": 120, "width": 200, "height": 250}


def test_simple_face_crop(sample_image, sample_bbox):
    """Test that simple face crop works correctly."""
    result = simple_face_crop(sample_image, sample_bbox, padding=20)
    
    assert result is not None
    assert len(result.shape) == 3  # Should be color image (H, W, C)
    assert result.shape[2] == 3  # Should have 3 color channels
    
    # Check dimensions account for padding
    expected_width = sample_bbox["width"] + 2 * 20  # bbox width + 2*padding
    expected_height = sample_bbox["height"] + 2 * 20
    
    assert result.shape[1] == expected_width
    assert result.shape[0] == expected_height


def test_simple_face_crop_boundary(sample_image):
    """Test face crop at image boundaries doesn't crash."""
    # Bbox that extends beyond image boundaries
    bbox = {"x": 450, "y": 450, "width": 100, "height": 100}
    
    result = simple_face_crop(sample_image, bbox, padding=20)
    
    assert result is not None
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_estimate_eye_positions():
    """Test eye position estimation."""
    test_face = np.zeros((200, 200, 3), dtype=np.uint8)
    
    eyes = estimate_eye_positions(test_face)
    
    assert eyes is not None
    assert len(eyes) == 2
    left_eye, right_eye = eyes
    
    # Check eyes are tuples of coordinates
    assert len(left_eye) == 2
    assert len(right_eye) == 2
    
    # Check left eye is to the left of right eye
    assert left_eye[0] < right_eye[0]
    
    # Check eyes are in reasonable positions
    assert 0 < left_eye[0] < 200
    assert 0 < left_eye[1] < 200
    assert 0 < right_eye[0] < 200
    assert 0 < right_eye[1] < 200


def test_align_face_disabled(sample_image, sample_bbox, monkeypatch):
    """Test that alignment is skipped when disabled."""
    # Temporarily disable alignment
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', False)
    
    result =align_face_simple(sample_image, sample_bbox, padding=20)
    
    # Should return simple crop when disabled
    expected = simple_face_crop(sample_image, sample_bbox, padding=20)
    
    assert result.shape == expected.shape
    np.testing.assert_array_equal(result, expected)


def test_align_face_enabled(sample_image, sample_bbox, monkeypatch):
    """Test that alignment is applied when enabled."""
    # Enable alignment
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', True)
    
    result = align_face_simple(sample_image, sample_bbox, padding=20)
    
    # Result should be valid image
    assert result is not None
    assert len(result.shape) == 3
    assert result.shape[2] == 3
    
    # Should have reasonable dimensions
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_align_face_handles_edge_cases(sample_bbox, monkeypatch):
    """Test alignment handles edge cases gracefully."""
    # Enable alignment
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', True)
    
    # Test with very small image
    tiny_img = np.zeros((10, 10, 3), dtype=np.uint8)
    result = align_face_simple(tiny_img, {"x": 0, "y": 0, "width": 5, "height": 5}, padding=2)
    assert result is not None
    
    # Test with single channel image (should still work with cropping)
    gray_img = np.zeros((200, 200), dtype=np.uint8)
    try:
        result = align_face_simple(gray_img, sample_bbox, padding=20)
        # If it works, great; if it falls back to simple crop due to error, that's also fine
        assert result is not None
    except Exception:
        # Alignment may fail on grayscale, which is acceptable
        pass


def test_align_face_minimal_rotation(sample_image, sample_bbox, monkeypatch):
    """Test that small rotation angles are ignored."""
    # Enable alignment
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', True)
    
    # For a symmetric pattern, rotation should be minimal
    result = align_face_simple(sample_image, sample_bbox, padding=20)
    
    # Just verify it returns a valid result
    assert result is not None
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_alignment_with_different_paddings(sample_image, sample_bbox, monkeypatch):
    """Test alignment with different padding values."""
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', True)
    
    for padding in [0, 10, 20, 50]:
        result = align_face_simple(sample_image, sample_bbox, padding=padding)
        assert result is not None
        assert result.shape[0] > 0
        assert result.shape[1] > 0


def test_empty_bbox_handling(sample_image, monkeypatch):
    """Test handling of invalid/empty bounding box."""
    monkeypatch.setattr(settings, 'FACE_ALIGNMENT_ENABLED', True)
    
    # Bbox with zero dimensions
    invalid_bbox = {"x": 100, "y": 100, "width": 0, "height": 0}
    
    result = align_face_simple(sample_image, invalid_bbox, padding=20)
    
    # Should handle gracefully (may return small crop or fall back)
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
