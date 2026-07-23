from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.SigLIP2Text import SigLIP2Text
from app.models.session_registry import (
    get_active_session_count,
    mark_model_session_inactive,
)

MODEL_PATH = "app/models/ONNX_Exports/SigLIP2_Base_Text.onnx"
MODEL_KEY = "siglip2_base_text"


class _FakeTensor:
    def __init__(self, name):
        self.name = name


def _ort_session(input_names, output_name="output"):
    """Stand-in for onnxruntime.InferenceSession -- no real model file needed."""
    session = MagicMock()
    session.get_inputs.return_value = [_FakeTensor(n) for n in input_names]
    session.get_outputs.return_value = [_FakeTensor(output_name)]
    return session


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    # Don't leak a registered session into other tests sharing this model key
    while get_active_session_count(MODEL_KEY) > 0:
        mark_model_session_inactive(MODEL_KEY)


class TestGetSession:
    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_second_call_returns_cached_session(self, mock_exists, mock_cls):
        mock_cls.return_value = _ort_session(["input_ids", "attention_mask"])
        model = SigLIP2Text(MODEL_PATH)

        first = model.get_session()
        second = model.get_session()  # fast path: self._session already set
        assert second == first
        model.close()

    def test_raises_if_names_cleared_mid_call(self):
        # session present but a racing close() has nulled the tensor names
        model = SigLIP2Text(MODEL_PATH)
        model._session = MagicMock()
        model.input_ids_name = None
        with pytest.raises(RuntimeError, match="was closed"):
            model.get_session()

    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_raises_when_output_name_missing(self, mock_exists, mock_cls):
        # Inputs valid, but the graph exposes no usable output tensor name
        mock_cls.return_value = _ort_session(
            ["input_ids", "attention_mask"], output_name=None
        )
        model = SigLIP2Text(MODEL_PATH)
        with pytest.raises(RuntimeError, match="was closed"):
            model.get_session()
        model.close()


class TestGetEmbedding:
    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_returns_l2_normalized_embedding(self, mock_exists, mock_cls):
        session = _ort_session(["input_ids", "attention_mask"])
        session.run.return_value = [np.array([[3.0, 4.0]], dtype=np.float32)]
        mock_cls.return_value = session

        model = SigLIP2Text(MODEL_PATH)
        ids = np.zeros((1, 4), dtype=np.int64)
        mask = np.ones((1, 4), dtype=np.int64)

        embedding = model.get_embedding(ids, mask)
        assert np.allclose(np.linalg.norm(embedding), 1.0)
        assert np.allclose(embedding, [0.6, 0.8])
        model.close()
