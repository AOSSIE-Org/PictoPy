import cv2
import numpy as np


def preprocess_image(image):
    image = cv2.resize(image, (160, 160))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)
    image = (image - 127.5) / 128.0
    return image

# Prepares the input image for the neural network by resizing, converting color space,
# rearranging dimensions, adding batch dimension, converting type to float32,
# and normalizing pixel values to roughly [-1, 1] range.


def normalize_embedding(embedding):
    return embedding / np.linalg.norm(embedding)

# Normalizes a face embedding vector to unit length (L2 norm = 1),
# which is useful for consistent comparison using cosine similarity.


def cosine_similarity(embedding1, embedding2):
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )

# Computes the cosine similarity between two embedding vectors,
# measuring how similar they are regardless of their magnitude.
