from __future__ import annotations
import os
import threading
import numpy as np
import onnxruntime
from app.models.model_registry import MODEL_REGISTRY, get_model_key_from_path
from app.models.session_registry import (
    mark_model_session_active,
    mark_model_session_inactive,
)
from app.utils.ONNX import ONNX_util_get_execution_providers
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class SigLIP2Vision:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model_key = get_model_key_from_path(model_path)
        self._session_registered = False
        self._session: onnxruntime.InferenceSession | None = None
        self.input_tensor_name: str | None = None
        self.output_tensor_name: str | None = None
        self._lock = threading.Lock()

    def get_session(self) -> tuple[onnxruntime.InferenceSession, str, str]:
        session = self._session
        if session is not None:
            input_name = self.input_tensor_name
            output_name = self.output_tensor_name
            if input_name is None or output_name is None:
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )
            return session, input_name, output_name

        with self._lock:
            if self._session is None:
                if not os.path.exists(self.model_path):
                    model_key = None
                    for key, spec in MODEL_REGISTRY.items():
                        if spec["filename"] in self.model_path:
                            model_key = key
                            break
                    model_name = (
                        model_key if model_key else os.path.basename(self.model_path)
                    )
                    raise RuntimeError(
                        f"Model '{model_name}' is not installed. "
                        "Please install it from Settings → AI Models before using this feature."
                    )

                self._session = onnxruntime.InferenceSession(
                    self.model_path, providers=ONNX_util_get_execution_providers()
                )
                if self._model_key is not None and not self._session_registered:
                    try:
                        mark_model_session_active(self._model_key)
                    except RuntimeError:
                        self._session = None
                        raise
                    self._session_registered = True
                self.input_tensor_name = self._session.get_inputs()[0].name
                self.output_tensor_name = self._session.get_outputs()[0].name

            session = self._session
            input_name = self.input_tensor_name
            output_name = self.output_tensor_name
            if session is None or input_name is None or output_name is None:
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )

        return session, input_name, output_name

    def get_embedding(self, pixel_values: np.ndarray) -> np.ndarray:
        """pixel_values: preprocessed [N, 3, H, W] float32 array.
        Returns [N, D] float32, each row L2-normalized -- normalized
        once here so downstream scoring never renormalizes the image
        side. Stored embeddings in image_embeddings are therefore
        unit-norm."""
        session, input_name, output_name = self.get_session()
        result = session.run([output_name], {input_name: pixel_values})[0]
        norms = np.linalg.norm(result, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        return (result / norms).astype(np.float32)

    def close(self):
        with self._lock:
            if self._session is not None:
                self._session = None
                self.input_tensor_name = None
                self.output_tensor_name = None
                if self._model_key is not None and self._session_registered:
                    mark_model_session_inactive(self._model_key)
                    self._session_registered = False
                logger.info("SigLIP2Vision model session closed.")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
