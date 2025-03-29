import cv2
import numpy as np
from numpy.typing import NDArray
from typing import Any, cast


def preprocess_image(image: NDArray[Any]) -> NDArray[Any]:
    image = cv2.resize(image, (160, 160))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)
    image = (image - 127.5) / 128.0
    return image


def normalize_embedding(embedding: NDArray[Any]) -> NDArray[Any]:
    norm = np.linalg.norm(embedding)
    normalized = embedding / norm
    return cast(NDArray[Any], normalized)


def cosine_similarity(embedding1: NDArray[Any], embedding2: NDArray[Any]) -> float:
    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )
    return float(similarity)
