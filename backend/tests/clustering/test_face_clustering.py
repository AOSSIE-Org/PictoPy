import numpy as np
from app.utils.face_clusters import _validate_embedding, _calculate_cosine_distances


def test_validate_embedding_valid():
    embedding = np.array([0.5, 0.4, 0.3])
    assert _validate_embedding(embedding) is True


def test_validate_embedding_zero_vector():
    embedding = np.array([0.0, 0.0, 0.0])
    assert _validate_embedding(embedding) is False


def test_validate_embedding_nan():
    embedding = np.array([0.1, np.nan, 0.3])
    assert _validate_embedding(embedding) is False


def test_calculate_cosine_distances_basic():
    face_embedding = np.array([1.0, 0.0])
    cluster_means = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])

    distances = _calculate_cosine_distances(face_embedding, cluster_means)

    # First cluster identical → distance close to 0
    assert distances[0] < 0.01

    # Second cluster orthogonal → distance close to 1
    assert 0.9 < distances[1] <= 1.0


def test_calculate_cosine_distances_zero_vector():
    face_embedding = np.array([0.0, 0.0])
    cluster_means = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])

    distances = _calculate_cosine_distances(face_embedding, cluster_means)

    # Zero vector should return max distances
    assert all(d == 1.0 for d in distances)