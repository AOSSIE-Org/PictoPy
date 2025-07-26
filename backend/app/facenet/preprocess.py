import cv2
import numpy as np


def preprocess_image(image):
    """
    Preprocess the input image for face embedding extraction.

    Steps:
    - Resize to 160x160 pixels
    - Convert color space from BGR to RGB
    - Rearrange dimensions to (channels, height, width)
    - Add batch dimension
    - Normalize pixel values to roughly [-1, 1]

    Args:
        image: Input image in BGR format (as loaded by OpenCV)

    Returns:
        Preprocessed image ready for model input.
    """
    image = cv2.resize(image, (160, 160))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)
    image = (image - 127.5) / 128.0
    return image


def normalize_embedding(embedding):
    """
    Normalize a face embedding vector to unit length.

    Args:
        embedding: Raw face embedding vector.

    Returns:
        L2-normalized embedding vector.
    """
    return embedding / np.linalg.norm(embedding)


def cosine_similarity(embedding1, embedding2):
    """
    Compute the cosine similarity between two embedding vectors.

    Args:
        embedding1: First embedding vector.
        embedding2: Second embedding vector.

    Returns:
        Cosine similarity score between -1 and 1.
    """
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )
