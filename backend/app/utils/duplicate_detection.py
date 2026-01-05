"""
Duplicate and "Best Shot" Detection Module.

This module provides functionality to:
1. Detect duplicate/similar images using perceptual hashing
2. Score image quality based on sharpness and exposure
3. Suggest the "best shot" from a group of similar images
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from PIL import Image

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImageQualityScore:
    """Represents the quality score of an image."""
    image_id: str
    image_path: str
    sharpness_score: float
    exposure_score: float
    overall_score: float


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate/similar images."""
    group_id: int
    images: List[Dict]
    best_shot_id: str
    best_shot_path: str


def compute_phash(image_path: str, hash_size: int = 16) -> Optional[np.ndarray]:
    """
    Compute perceptual hash (pHash) for an image.
    
    pHash is robust to minor changes like resizing, compression, and slight color adjustments.
    
    Args:
        image_path: Path to the image file
        hash_size: Size of the hash (default 16 for 256-bit hash)
    
    Returns:
        Binary hash array or None if image cannot be processed
    """
    try:
        # Read image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.warning(f"Could not read image: {image_path}")
            return None
        
        # Resize to hash_size + 1 for DCT
        resized = cv2.resize(img, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
        
        # Compute DCT (Discrete Cosine Transform)
        dct = cv2.dct(np.float32(resized))
        
        # Use top-left hash_size x hash_size of DCT (low frequencies)
        dct_low = dct[:hash_size, :hash_size]
        
        # Compute median and create binary hash
        median = np.median(dct_low)
        phash = (dct_low > median).flatten().astype(np.uint8)
        
        return phash
    except Exception as e:
        logger.error(f"Error computing pHash for {image_path}: {e}")
        return None


def compute_hash_distance(hash1: np.ndarray, hash2: np.ndarray) -> int:
    """
    Compute Hamming distance between two hashes.
    
    Args:
        hash1: First hash array
        hash2: Second hash array
    
    Returns:
        Hamming distance (number of differing bits)
    """
    return np.sum(hash1 != hash2)


def calculate_sharpness(image_path: str) -> float:
    """
    Calculate image sharpness using Laplacian variance.
    
    Higher values indicate sharper images (less blur).
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Sharpness score (Laplacian variance)
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        
        # Compute Laplacian variance
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        variance = laplacian.var()
        
        return float(variance)
    except Exception as e:
        logger.error(f"Error calculating sharpness for {image_path}: {e}")
        return 0.0


def calculate_exposure_score(image_path: str) -> float:
    """
    Calculate exposure quality score.
    
    Measures how well-exposed an image is by analyzing histogram distribution.
    Penalizes over-exposed (too bright) and under-exposed (too dark) images.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Exposure score (0-1, higher is better)
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0.0
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()  # Normalize
        
        # Calculate mean brightness
        mean_brightness = np.sum(np.arange(256) * hist)
        
        # Ideal brightness is around 128 (middle of range)
        # Score decreases as we move away from ideal
        brightness_score = 1.0 - abs(mean_brightness - 128) / 128
        
        # Calculate contrast (standard deviation of histogram)
        std_brightness = np.sqrt(np.sum(((np.arange(256) - mean_brightness) ** 2) * hist))
        
        # Good contrast is around 50-80
        contrast_score = min(std_brightness / 60, 1.0)
        
        # Check for clipping (over/under exposure)
        dark_pixels = np.sum(hist[:10])  # Very dark pixels
        bright_pixels = np.sum(hist[245:])  # Very bright pixels
        clipping_penalty = 1.0 - (dark_pixels + bright_pixels)
        
        # Combined exposure score
        exposure_score = (brightness_score * 0.4 + contrast_score * 0.3 + clipping_penalty * 0.3)
        
        return max(0.0, min(1.0, exposure_score))
    except Exception as e:
        logger.error(f"Error calculating exposure for {image_path}: {e}")
        return 0.0


def calculate_image_quality(image_id: str, image_path: str) -> ImageQualityScore:
    """
    Calculate overall quality score for an image.
    
    Args:
        image_id: Unique identifier for the image
        image_path: Path to the image file
    
    Returns:
        ImageQualityScore with individual and overall scores
    """
    sharpness = calculate_sharpness(image_path)
    exposure = calculate_exposure_score(image_path)
    
    # Normalize sharpness to 0-1 range (typical values are 0-1000+)
    # Using log scale to handle wide range of values
    normalized_sharpness = min(1.0, np.log1p(sharpness) / 10)
    
    # Overall score: weighted combination
    # Sharpness is more important for "best shot" selection
    overall = normalized_sharpness * 0.6 + exposure * 0.4
    
    return ImageQualityScore(
        image_id=image_id,
        image_path=image_path,
        sharpness_score=sharpness,
        exposure_score=exposure,
        overall_score=overall
    )


def find_duplicate_groups(
    images: List[Dict],
    similarity_threshold: int = 10
) -> List[DuplicateGroup]:
    """
    Find groups of duplicate/similar images.
    
    Args:
        images: List of image dictionaries with 'id' and 'path' keys
        similarity_threshold: Maximum Hamming distance to consider images as duplicates
                            (lower = stricter matching, default 10 for ~96% similarity)
    
    Returns:
        List of DuplicateGroup objects containing similar images
    """
    if not images:
        return []
    
    logger.info(f"Finding duplicates among {len(images)} images...")
    
    # Compute hashes for all images
    image_hashes: List[Tuple[Dict, Optional[np.ndarray]]] = []
    for img in images:
        phash = compute_phash(img['path'])
        image_hashes.append((img, phash))
    
    # Filter out images where hash computation failed
    valid_images = [(img, h) for img, h in image_hashes if h is not None]
    
    if len(valid_images) < 2:
        return []
    
    # Find similar images using Union-Find approach
    n = len(valid_images)
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Compare all pairs
    for i in range(n):
        for j in range(i + 1, n):
            distance = compute_hash_distance(valid_images[i][1], valid_images[j][1])
            if distance <= similarity_threshold:
                union(i, j)
    
    # Group images by their root parent
    groups_dict = defaultdict(list)
    for i in range(n):
        root = find(i)
        groups_dict[root].append(valid_images[i][0])
    
    # Filter groups with more than one image and find best shot
    duplicate_groups = []
    group_id = 0
    
    for images_in_group in groups_dict.values():
        if len(images_in_group) > 1:
            # Calculate quality scores for all images in group
            quality_scores = [
                calculate_image_quality(img['id'], img['path'])
                for img in images_in_group
            ]
            
            # Find best shot (highest overall score)
            best_shot = max(quality_scores, key=lambda x: x.overall_score)
            
            duplicate_groups.append(DuplicateGroup(
                group_id=group_id,
                images=images_in_group,
                best_shot_id=best_shot.image_id,
                best_shot_path=best_shot.image_path
            ))
            group_id += 1
    
    logger.info(f"Found {len(duplicate_groups)} duplicate groups")
    return duplicate_groups


def get_duplicate_groups_with_scores(
    images: List[Dict],
    similarity_threshold: int = 10
) -> List[Dict]:
    """
    Get duplicate groups with detailed quality scores for each image.
    
    Args:
        images: List of image dictionaries with 'id' and 'path' keys
        similarity_threshold: Maximum Hamming distance for duplicates
    
    Returns:
        List of dictionaries containing group info and quality scores
    """
    groups = find_duplicate_groups(images, similarity_threshold)
    
    result = []
    for group in groups:
        # Calculate detailed scores for each image
        images_with_scores = []
        for img in group.images:
            score = calculate_image_quality(img['id'], img['path'])
            images_with_scores.append({
                'id': img['id'],
                'path': img['path'],
                'thumbnailPath': img.get('thumbnailPath', ''),
                'sharpness_score': round(score.sharpness_score, 2),
                'exposure_score': round(score.exposure_score, 4),
                'overall_score': round(score.overall_score, 4),
                'is_best_shot': img['id'] == group.best_shot_id
            })
        
        # Sort by overall score descending
        images_with_scores.sort(key=lambda x: x['overall_score'], reverse=True)
        
        result.append({
            'group_id': group.group_id,
            'image_count': len(group.images),
            'best_shot_id': group.best_shot_id,
            'images': images_with_scores
        })
    
    return result
