from unittest.mock import MagicMock, patch

import pytest

from app.models.SigLIP2Text import SigLIP2Text
from app.models.session_registry import (
    get_active_session_count,
    mark_model_session_inactive,
)

MODEL_PATH = "app/models/ONNX_Exports/SigLIP2_Base_Text.onnx"
MODEL_KEY = "siglip2_base_text"


class _FakeTensor:
    def __init__(self, name: str):
        self.name = name


def _mock_ort_session(input_names: list[str]) -> MagicMock:
    """Stand-in for onnxruntime.InferenceSession -- these tests exercise
    close()/session_registry bookkeeping, not real inference, and must not
    depend on the actual (multi-hundred-MB, not checked into git) ONNX
    model file existing on disk."""
    session = MagicMock()
    session.get_inputs.return_value = [_FakeTensor(name) for name in input_names]
    session.get_outputs.return_value = [_FakeTensor("output")]
    return session


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    # Belt-and-suspenders: don't let a failed assertion mid-test leak a
    # registered session into other tests sharing this real model key. A
    # fresh SigLIP2Text(...).close() is a no-op here (its _session_registered
    # starts False), so decrement the registry directly instead.
    while get_active_session_count(MODEL_KEY) > 0:
        mark_model_session_inactive(MODEL_KEY)


class TestONNXSessionBaseClose:
    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_normal_close_decrements_active_count(self, mock_exists, mock_session_cls):
        mock_session_cls.return_value = _mock_ort_session(
            ["input_ids", "attention_mask"]
        )

        session = SigLIP2Text(MODEL_PATH)
        session.get_session()
        assert get_active_session_count(MODEL_KEY) == 1

        session.close()
        assert get_active_session_count(MODEL_KEY) == 0

    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_close_releases_registration_after_validation_failure(
        self, mock_exists, mock_session_cls
    ):
        """Regression test: get_session() can register the session (via
        mark_model_session_active) and then null self._session on a
        tensor-name validation failure, while leaving _session_registered
        True. close() must still release the registration in that state --
        gating cleanup on `self._session is not None` would leak the active
        count forever and permanently block this model from uninstalling."""
        # Missing input_ids/attention_mask -> SigLIP2Text's own validation
        # raises after _create_session() has already registered the session.
        mock_session_cls.return_value = _mock_ort_session(["wrong_name"])

        session = SigLIP2Text(MODEL_PATH)

        with pytest.raises(RuntimeError):
            session.get_session()

        # The leak precondition: registered, but no live session.
        assert session._session is None
        assert session._session_registered is True
        assert get_active_session_count(MODEL_KEY) == 1

        session.close()

        assert get_active_session_count(MODEL_KEY) == 0
        assert session._session_registered is False

    @patch("os.path.exists", return_value=False)
    def test_close_is_a_noop_when_never_opened(self, mock_exists):
        session = SigLIP2Text(MODEL_PATH)
        session.close()  # must not raise
        assert get_active_session_count(MODEL_KEY) == 0

    @patch("onnxruntime.InferenceSession")
    @patch("os.path.exists", return_value=True)
    def test_close_is_idempotent(self, mock_exists, mock_session_cls):
        mock_session_cls.return_value = _mock_ort_session(
            ["input_ids", "attention_mask"]
        )

        session = SigLIP2Text(MODEL_PATH)
        session.get_session()
        session.close()
        session.close()  # second call must not raise or double-decrement
        assert get_active_session_count(MODEL_KEY) == 0
