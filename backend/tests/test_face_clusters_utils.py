import numpy as np
import pytest

from app.utils.face_clusters import _validate_embedding


def test_validate_embedding_valid_vector():
    """
    Should return True for a normal non-zero finite embedding.
    """
    embedding = np.array([0.5, 0.2, 0.1])
    assert _validate_embedding(embedding) is True


def test_validate_embedding_zero_vector():
    """
    Should return False for zero vector (norm too small).
    """
    embedding = np.zeros(128)
    assert _validate_embedding(embedding) is False


def test_validate_embedding_nan_values():
    """
    Should return False if embedding contains NaN.
    """
    embedding = np.array([0.1, np.nan, 0.3])
    assert _validate_embedding(embedding) is False


def test_validate_embedding_inf_values():
    """
    Should return False if embedding contains infinite values.
    """
    embedding = np.array([0.1, np.inf, 0.3])
    assert _validate_embedding(embedding) is False


def test_validate_embedding_small_norm():
    """
    Should return False if norm is below threshold.
    """
    embedding = np.array([1e-12, 1e-12, 1e-12])
    assert _validate_embedding(embedding, min_norm=1e-6) is False


def test_validate_embedding_custom_min_norm():
    """
    Should respect custom min_norm parameter.
    """
    embedding = np.array([0.01, 0.01, 0.01])
    assert _validate_embedding(embedding, min_norm=0.1) is False