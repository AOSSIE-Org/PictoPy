import imagehash
from PIL import Image
import os
import json
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Constants
# dHash is generally faster and better at gradients than pHash for burst shots
HASH_SIZE = 8 
HASH_THRESHOLD = 8 # Strict threshold for hashing
MIN_MATCH_COUNT = 15 # Minimum shared keypoints to consider them the same scene

def get_image_sharpness(image_path: str) -> float:
    """
    Returns a score representing the 'sharpness' of an image.
    Higher is better.
    Technique: Laplacian Variance (Detects edges).
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance
        # Blurry images have low variance (few edges), Sharp images have high variance
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance
    except Exception as e:
        logger.error(f"Error calculating sharpness for {image_path}: {e}")
        return 0.0

def are_images_geometrically_similar(path1: str, path2: str) -> bool:
    """
    Uses ORB (Oriented FAST and Rotated BRIEF) to detect if two images 
    are of the same scene, even if camera moved slightly or angle changed.
    """
    try:
        img1 = cv2.imread(path1, 0) # Read as grayscale
        img2 = cv2.imread(path2, 0)
        
        if img1 is None or img2 is None:
            return False

        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=500)

        # Find keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            return False

        # Match descriptors using BFMatcher (Brute Force) with Hamming distance
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        # Sort matches by distance (best matches first)
        matches = sorted(matches, key=lambda x: x.distance)

        # Take top 15% of matches or top 50 matches
        good_matches = [m for m in matches if m.distance < 50]

        # If we have enough strong geometrical matches, it's the same object/scene
        return len(good_matches) > MIN_MATCH_COUNT

    except Exception as e:
        logger.error(f"Error matching features between {path1} and {path2}: {e}")
        return False


def calculate_phash(image_path: str) -> Optional[str]:
    """
    Calculate perceptual hash for an image.
    """
    try:
        img = Image.open(image_path)
        # phash is generally good for finding duplicates including resized/compressed ones
        hash_obj = imagehash.phash(img)
        return str(hash_obj)
    except Exception as e:
        logger.error(f"Error calculating pHash for {image_path}: {e}")
        return None

def identify_best_shot(images: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Identify the best shot from a list of duplicate images.
    Heuristic: Sharpness (Laplacian Variance), then File Size.
    """
    if not images:
        return None

    # Calculate sharpness for all if not already calculated
    for img in images:
        if 'sharpness_score' not in img:
            img['sharpness_score'] = get_image_sharpness(img['path'])

    # Pick best image
    # Heuristic: Sharpness is king.
    # Tie-breaker: File size (higher usually means more color data if sharpness is equal)
    try:
        best_image = max(images, key=lambda x: (x.get('sharpness_score', 0), os.path.getsize(x['path']) if os.path.exists(x['path']) else 0))
        return best_image
    except Exception as e:
        logger.error(f"Error identifying best shot: {e}")
        return images[0] if images else None

def group_similar_images(images: List[Dict[str, Any]], threshold: int = HASH_THRESHOLD) -> List[List[Dict[str, Any]]]:
    """
    Groups images by Visual Hash (dHash) and verifies with ORB.
    """
    clusters = []
    
    # Pre-compute dHash (Difference Hash) instead of pHash
    processed_images = []
    for img in images:
        if img.get('phash'): # We are technically using the pHash from DB if available, or calculating on fly
             # If we want to switch to dHash strictly we might need to re-compute.
             # For now let's reuse the stored hash as a first pass filter if possible,
             # OR strictly compute dHash now for better burst mode detection.
             # Given the context, let's calculate dHash on fly for high accuracy as requested.
             pass
        
        path = img.get('path')
        if not path or not os.path.exists(path):
            continue
            
        try:
             # Calculate dHash on the fly for heavy logic mode
             pil_img = Image.open(path)
             dhash = imagehash.dhash(pil_img, hash_size=HASH_SIZE)
             img['hash_obj'] = dhash
             # Compute sharpness now to save time later
             img['sharpness_score'] = get_image_sharpness(path)
             processed_images.append(img)
        except Exception as e:
             logger.warning(f"Error processing image {path}: {e}")

    # Sort by sharpness initially so the "best" image often becomes the cluster rep
    processed_images.sort(key=lambda x: x.get('sharpness_score', 0), reverse=True)
    
    # Greedy clustering
    for img in processed_images:
        found_cluster = False
        img_hash = img['hash_obj']
        
        for cluster in clusters:
            if not cluster:
                continue
                
            rep_img = cluster[0]
            rep_hash = rep_img['hash_obj']
            
            dist = img_hash - rep_hash
            
            # Fast Check: Hamming Distance
            if dist <= threshold:
                # Secondary Check: ORB Verification
                # We check geometric similarity if the hash is "close but not perfect" or just always.
                # To be robust as requested:
                if are_images_geometrically_similar(img['path'], rep_img['path']):
                    cluster.append(img)
                    found_cluster = True
                    break
        
        if not found_cluster:
            clusters.append([img])
            
    # Filter out single-image clusters (no duplicates)
    duplicate_groups = [cluster for cluster in clusters if len(cluster) > 1]
    
    # Remove temporary objects
    for group in duplicate_groups:
        for img in group:
            img.pop('hash_obj', None)
                
    return duplicate_groups

