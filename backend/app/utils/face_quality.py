"""
Face Quality Assessment Module

This module provides functions to assess the quality of detected faces
based on multiple criteria including sharpness, brightness, and size.
High-quality faces lead to better embeddings and improved clustering accuracy.
"""

import cv2
import numpy as np
from typing import Dict
from numpy.typing import NDArray


def assess_face_sharpness(face_image: NDArray) -> float:
    """
    Assess face sharpness using Laplacian variance.

    The Laplacian operator detects edges in the image. A blurry image
    has low variance in the Laplacian, while a sharp image has high variance.

    Args:
        face_image: Face image as numpy array (BGR or RGB)

    Returns:
        Sharpness score (0.0 = very blurry, 1.0 = very sharp)
    """
    # Convert to grayscale if needed
    if len(face_image.shape) == 3:
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_image

    # Calculate Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Normalize to 0-1 scale (empirical threshold: 100 is reasonable sharpness)
    # Values > 100 are sharp, values < 50 are blurry
    sharpness_score = min(laplacian_var / 100.0, 1.0)

    return float(sharpness_score)


def assess_face_brightness(face_image: NDArray) -> float:
    """
    Assess face brightness distribution.

    Faces should have moderate brightness (not too dark, not overexposed).
    This function evaluates how close the average brightness is to ideal (128).

    Args:
        face_image: Face image as numpy array (BGR or RGB)

    Returns:
        Brightness score (0.0 = very dark/bright, 1.0 = optimal)
    """
    # Convert to grayscale if needed
    if len(face_image.shape) == 3:
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_image

    # Calculate mean brightness
    mean_brightness = np.mean(gray)

    # Optimal brightness is around 128 (middle of 0-255)
    # Calculate deviation from optimal
    deviation = abs(mean_brightness - 128.0)

    # Convert to score (0 deviation = 1.0, 128 deviation = 0.0)
    brightness_score = 1.0 - (deviation / 128.0)

    return float(brightness_score)


def assess_face_size(face_image: NDArray, target_size: int = 160) -> float:
    """
    Assess face size relative to expected input size.

    Larger faces generally produce better embeddings because they contain
    more detail. This function scores based on how close the face is to
    or exceeds the target processing size.

    Args:
        face_image: Face image as numpy array
        target_size: Expected face size for model (default: 160 for FaceNet)

    Returns:
        Size score (0.0 = very small, 1.0 = good size or larger)
    """
    height, width = face_image.shape[:2]

    # Use the smaller dimension
    min_dimension = min(height, width)

    # Calculate size score (normalized by target)
    size_ratio = min_dimension / target_size

    # Cap at 1.0 (larger than target is still good)
    size_score = min(size_ratio, 1.0)

    return float(size_score)


def calculate_face_quality(
    face_image: NDArray,
    sharpness_weight: float = 0.4,
    brightness_weight: float = 0.3,
    size_weight: float = 0.3,
) -> Dict[str, float]:
    """
    Calculate overall face quality score based on multiple criteria.

    This is the main function that combines all quality metrics into
    a single overall score. Individual component scores are also returned
    for debugging and analysis.

    Args:
        face_image: Face image as numpy array
        sharpness_weight: Weight for sharpness component (default: 0.4)
        brightness_weight: Weight for brightness component (default: 0.3)
        size_weight: Weight for size component (default: 0.3)

    Returns:
        Dictionary containing:
            - quality: Overall quality score (0.0 - 1.0)
            - sharpness: Sharpness score (0.0 - 1.0)
            - brightness: Brightness score (0.0 - 1.0)
            - size: Size score (0.0 - 1.0)
    """
    # Validate weights sum to 1.0
    total_weight = sharpness_weight + brightness_weight + size_weight
    if not np.isclose(total_weight, 1.0):
        raise ValueError(
            f"Weights must sum to 1.0, got {total_weight}. "
            f"sharpness={sharpness_weight}, brightness={brightness_weight}, size={size_weight}"
        )

    # Calculate individual scores
    sharpness = assess_face_sharpness(face_image)
    brightness = assess_face_brightness(face_image)
    size = assess_face_size(face_image)

    # Calculate weighted overall score
    overall_quality = (
        sharpness * sharpness_weight
        + brightness * brightness_weight
        + size * size_weight
    )

    return {
        "quality": float(overall_quality),
        "sharpness": float(sharpness),
        "brightness": float(brightness),
        "size": float(size),
    }


def should_include_face(quality_score: float, min_threshold: float = 0.4) -> bool:
    """
    Determine if a face should be included based on quality threshold.

    Args:
        quality_score: Overall quality score (0.0 - 1.0)
        min_threshold: Minimum acceptable quality (default: 0.4)

    Returns:
        True if face meets quality threshold, False otherwise
    """
    return quality_score >= min_threshold


def filter_quality_faces(faces_data: list, min_quality: float = 0.4) -> list:
    """
    Filter a list of faces by quality threshold.

    Args:
        faces_data: List of face dictionaries with 'quality' key
        min_quality: Minimum acceptable quality score

    Returns:
        Filtered list of faces meeting quality threshold
    """
    return [face for face in faces_data if face.get("quality", 0.0) >= min_quality]


# Example usage and testing
if __name__ == "__main__":
    # Test with a sample image
    import sys

    if len(sys.argv) > 1:
        img = cv2.imread(sys.argv[1])
        if img is not None:
            result = calculate_face_quality(img)
            print("Face Quality Assessment:")
            print(f"  Overall Quality: {result['quality']:.3f}")
            print(f"  Sharpness:      {result['sharpness']:.3f}")
            print(f"  Brightness:     {result['brightness']:.3f}")
            print(f"  Size:           {result['size']:.3f}")
            print(f"  Include Face:   {should_include_face(result['quality'])}")
        else:
            print(f"Could not load image: {sys.argv[1]}")
    else:
        print("Usage: python face_quality.py <image_path>")
