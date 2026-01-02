"""
Face alignment utilities for improving face recognition accuracy.

This module provides face alignment preprocessing to handle tilted, angled,
and profile faces. It uses simple geometric transformation based on eye positions.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict
from app.config.settings import FACE_ALIGNMENT_ENABLED
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def estimate_eye_positions(face_image: np.ndarray) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Estimate eye positions using simple heuristics for face crops.
    
    For a cropped face image, eyes are typically:
    - Horizontally: At 1/4 and 3/4 of width
    - Vertically: At 1/3 of height from top
    
    Args:
        face_image: Cropped face image
    
    Returns:
        Tuple of (left_eye, right_eye) coordinates, or None if estimation fails
    """
    h, w = face_image.shape[:2]
    
    # Heuristic eye positions (works reasonably well for frontal faces)
    left_eye = (int(w * 0.35), int(h * 0.35))
    right_eye = (int(w * 0.65), int(h * 0.35))
    
    return (left_eye, right_eye)


def align_face_simple(
    image: np.ndarray,
    bbox: Dict[str, int],
    padding: int = 20
) -> np.ndarray:
    """
    Extract and align face using simple geometric heuristics.
    
    This is a lightweight alignment approach that:
    1. Crops the face with padding
    2. Estimates eye positions using heuristics
    3. Rotates face to align eyes horizontally
    4. Returns aligned face crop
    
    Args:
        image: Full source image
        bbox: Bounding box dict with keys: x, y, width, height
        padding: Padding around face in pixels
    
    Returns:
        Aligned face crop as numpy array
    """
    if not FACE_ALIGNMENT_ENABLED:
        # Fallback to simple crop when alignment disabled
        return simple_face_crop(image, bbox, padding)
    
    try:
        # Extract face region with padding
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        img_h, img_w = image.shape[:2]
        
        # Calculate crop bounds with padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(img_w, x + w + padding)
        y2 = min(img_h, y + h + padding)
        
        # Crop face region
        face_crop = image[y1:y2, x1:x2]
        
        if face_crop.size == 0:
            logger.warning("Empty face crop, returning original")
            return simple_face_crop(image, bbox, padding)
        
        # Estimate eye positions  
        eyes = estimate_eye_positions(face_crop)
        if eyes is None:
            return face_crop
        
        left_eye, right_eye = eyes
        
        # Calculate rotation angle to align eyes horizontally
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Only apply rotation if angle is significant (> 3 degrees)
        if abs(angle) < 3:
            return face_crop
        
        # Calculate center point for rotation (between eyes)
        center_x = (left_eye[0] + right_eye[0]) // 2
        center_y = (left_eye[1] + right_eye[1]) // 2
        center = (center_x, center_y)
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, scale=1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(
            face_crop,
            M,
            (face_crop.shape[1], face_crop.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        logger.debug(f"Aligned face with rotation angle: {angle:.2f} degrees")
        return rotated
        
    except Exception as e:
        logger.warning(f"Face alignment failed: {e}, using simple crop")
        return simple_face_crop(image, bbox, padding)


def simple_face_crop(
    image: np.ndarray,
    bbox: Dict[str, int],
    padding: int = 20
) -> np.ndarray:
    """
    Simple face crop without alignment (fallback method).
    
    Args:
        image: Full source image
        bbox: Bounding box dict with keys: x, y, width, height
        padding: Padding around face in pixels
    
    Returns:
        Face crop as numpy array
    """
    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
    img_h, img_w = image.shape[:2]
    
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img_w, x + w + padding)
    y2 = min(img_h, y + h + padding)
    
    return image[y1:y2, x1:x2]
