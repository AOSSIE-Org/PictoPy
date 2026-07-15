from __future__ import annotations

import os
import threading
import onnxruntime

from app.models.model_registry import get_model_key_from_path
from app.models.session_registry import (
    mark_model_session_active,
    mark_model_session_inactive,
)
from app.utils.ONNX import ONNX_util_get_execution_providers
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class ONNXSessionBase:
    """Shared lazy-session/threading-lock/session_registry lifecycle for
    SigLIP2Vision and SigLIP2Text.

    Subclasses implement `get_session()` themselves (return arity differs
    per model), but must snapshot `self._session` and their tensor-name
    attributes into locals *before* releasing `_lock`, then return those
    locals -- never re-read `self.*` after the lock is released. A
    concurrent `close()` can otherwise flip attributes to None between the
    in-lock check and an out-of-lock return, handing the caller a session
    paired with a None tensor name.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model_key = get_model_key_from_path(model_path)
        self._session_registered = False
        self._session: onnxruntime.InferenceSession | None = None
        self._lock = threading.Lock()

    def _create_session(self) -> onnxruntime.InferenceSession:
        """Create and register a new ONNX session. Does not touch
        self._session -- caller assigns it only after this returns
        successfully, so a registration failure never leaves a
        half-initialized session in place."""
        if not os.path.exists(self.model_path):
            model_name = self._model_key or os.path.basename(self.model_path)
            raise RuntimeError(
                f"Model '{model_name}' is not installed. "
                "Please install it from Settings → AI Models before using this feature."
            )

        session = onnxruntime.InferenceSession(
            self.model_path, providers=ONNX_util_get_execution_providers()
        )
        if self._model_key is not None and not self._session_registered:
            mark_model_session_active(self._model_key)
            self._session_registered = True
        return session

    def _clear_tensor_names(self) -> None:
        """Subclasses null their tensor-name attributes here."""
        raise NotImplementedError

    def close(self) -> None:
        with self._lock:
            if self._session is not None:
                self._session = None
                self._clear_tensor_names()
                if self._model_key is not None and self._session_registered:
                    mark_model_session_inactive(self._model_key)
                    self._session_registered = False
                logger.info(f"{type(self).__name__} model session closed.")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
