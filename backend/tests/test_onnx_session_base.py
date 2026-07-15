from unittest.mock import patch

import onnxruntime
import pytest

from app.models.SigLIP2Text import SigLIP2Text
from app.models.session_registry import get_active_session_count

MODEL_PATH = "app/models/ONNX_Exports/SigLIP2_Base_Text.onnx"
MODEL_KEY = "siglip2_base_text"


class _FakeInput:
    def __init__(self, name: str):
        self.name = name


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    # Belt-and-suspenders: don't let a failed assertion mid-test leak a
    # registered session into other tests sharing this real model key.
    if get_active_session_count(MODEL_KEY) > 0:
        SigLIP2Text(MODEL_PATH).close()


class TestONNXSessionBaseClose:
    def test_normal_close_decrements_active_count(self):
        session = SigLIP2Text(MODEL_PATH)
        session.get_session()
        assert get_active_session_count(MODEL_KEY) == 1

        session.close()
        assert get_active_session_count(MODEL_KEY) == 0

    def test_close_releases_registration_after_validation_failure(self):
        """Regression test: get_session() can register the session (via
        mark_model_session_active) and then null self._session on a
        tensor-name validation failure, while leaving _session_registered
        True. close() must still release the registration in that state --
        gating cleanup on `self._session is not None` would leak the active
        count forever and permanently block this model from uninstalling."""
        session = SigLIP2Text(MODEL_PATH)

        with patch.object(
            onnxruntime.InferenceSession,
            "get_inputs",
            return_value=[_FakeInput("wrong_name")],
        ):
            with pytest.raises(RuntimeError):
                session.get_session()

        # The leak precondition: registered, but no live session.
        assert session._session is None
        assert session._session_registered is True
        assert get_active_session_count(MODEL_KEY) == 1

        session.close()

        assert get_active_session_count(MODEL_KEY) == 0
        assert session._session_registered is False

    def test_close_is_a_noop_when_never_opened(self):
        session = SigLIP2Text(MODEL_PATH)
        session.close()  # must not raise
        assert get_active_session_count(MODEL_KEY) == 0

    def test_close_is_idempotent(self):
        session = SigLIP2Text(MODEL_PATH)
        session.get_session()
        session.close()
        session.close()  # second call must not raise or double-decrement
        assert get_active_session_count(MODEL_KEY) == 0
