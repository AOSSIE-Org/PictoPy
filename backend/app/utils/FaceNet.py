"""
FaceNet Face Recognition Utilities

This module provides utility functions for FaceNet-based face recognition in PictoPy.
It handles image preprocessing, embedding normalization, and similarity computation
for face clustering and recognition tasks.

Key Features:
- Image preprocessing for FaceNet model input
- Face embedding normalization for consistent similarity computation
- Cosine similarity calculation for face matching
- Model path resolution for FaceNet models

The module supports the standard FaceNet preprocessing pipeline which includes
resizing to 160x160, color space conversion, normalization, and batch preparation.
"""

# Standard library imports
import cv2
import numpy as np

# Application imports
from app.config.settings import DEFAULT_FACENET_MODEL


# =============================================================================
# IMAGE PREPROCESSING
# =============================================================================

def FaceNet_util_preprocess_image(image):
    """
    Preprocess an image for FaceNet model input.
    
    This function applies the standard FaceNet preprocessing pipeline:
    1. Resize image to 160x160 pixels (FaceNet input size)
    2. Convert from BGR to RGB color space
    3. Transpose dimensions from HWC to CHW format
    4. Add batch dimension
    5. Convert to float32 and normalize to [-1, 1] range
    
    Args:
        image: Input image as numpy array in BGR format
        
    Returns:
        Preprocessed image ready for FaceNet model inference
    """
    # Resize to FaceNet input size (160x160)
    image = cv2.resize(image, (160, 160))
    
    # Convert from BGR to RGB color space
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Transpose from HWC to CHW format (channels first)
    image = image.transpose((2, 0, 1))
    
    # Add batch dimension (1, C, H, W)
    image = np.expand_dims(image, axis=0)
    
    # Convert to float32 and normalize to [-1, 1] range
    image = image.astype(np.float32)
    image = (image - 127.5) / 128.0
    
    return image


# =============================================================================
# EMBEDDING UTILITIES
# =============================================================================

def FaceNet_util_normalize_embedding(embedding):
    """
    Normalize a face embedding to unit length.
    
    This function normalizes the face embedding vector to have unit length,
    which is essential for accurate cosine similarity computation.
    
    Args:
        embedding: Face embedding vector
        
    Returns:
        Normalized embedding vector with unit length
    """
    return embedding / np.linalg.norm(embedding)


def FaceNet_util_cosine_similarity(embedding1, embedding2):
    """
    Compute cosine similarity between two face embeddings.
    
    Cosine similarity measures the cosine of the angle between two vectors,
    providing a value between -1 and 1. Values closer to 1 indicate higher
    similarity between faces.
    
    Args:
        embedding1: First face embedding vector
        embedding2: Second face embedding vector
        
    Returns:
        Cosine similarity value between -1 and 1
    """
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

def FaceNet_util_get_model_path():
    """
    Get the path to the FaceNet model file.
    
    Returns:
        str: Path to the default FaceNet model file
    """
    return DEFAULT_FACENET_MODEL
