import cv2
import numpy as np


def preprocess_image(image):
    image = cv2.resize(image, (160, 160))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32)
    image /= 255.0
    return image

def normalize_embedding(embedding):
    return embedding / np.linalg.norm(embedding)

def cosine_similarity(embedding1, embedding2):
    return np.dot(embedding1, embedding2)

