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


class SigLIP2Text:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model_key = get_model_key_from_path(model_path)
        self._session_registered = False
        self._session: onnxruntime.InferenceSession | None = None
        self.input_ids_name: str | None = None
        self.attention_mask_name: str | None = None
        self.output_tensor_name: str | None = None
        self._lock = threading.Lock()

    def get_session(self) -> tuple[onnxruntime.InferenceSession, str, str, str]:
        session = self._session
        if session is not None:
            if None in (
                self.input_ids_name,
                self.attention_mask_name,
                self.output_tensor_name,
            ):
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )
            return (
                session,
                self.input_ids_name,
                self.attention_mask_name,
                self.output_tensor_name,
            )

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

                input_names = {inp.name for inp in self._session.get_inputs()}
                self.input_ids_name = (
                    "input_ids" if "input_ids" in input_names else None
                )
                self.attention_mask_name = (
                    "attention_mask" if "attention_mask" in input_names else None
                )
                if self.input_ids_name is None or self.attention_mask_name is None:
                    self._session = None
                    raise RuntimeError(
                        f"SigLIP2Text ONNX graph at '{self.model_path}' does not expose the "
                        f"expected input_ids/attention_mask names; found: {input_names}"
                    )
                self.output_tensor_name = self._session.get_outputs()[0].name

            session = self._session
            if session is None or None in (
                self.input_ids_name,
                self.attention_mask_name,
                self.output_tensor_name,
            ):
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )

        return (
            session,
            self.input_ids_name,
            self.attention_mask_name,
            self.output_tensor_name,
        )

    def get_embedding(
        self, input_ids: np.ndarray, attention_mask: np.ndarray
    ) -> np.ndarray:
        """input_ids, attention_mask: [1, max_length] int64 arrays from
        the HF tokenizer -- this graph does not tokenize internally.
        Returns an L2-normalized embedding."""
        session, input_ids_name, attention_mask_name, output_name = self.get_session()
        result = session.run(
            [output_name],
            {input_ids_name: input_ids, attention_mask_name: attention_mask},
        )[0]
        embedding = result[0]
        norm = np.linalg.norm(embedding)
        return embedding / norm if norm > 0 else embedding

    def close(self):
        with self._lock:
            if self._session is not None:
                self._session = None
                self.input_ids_name = None
                self.attention_mask_name = None
                self.output_tensor_name = None
                if self._model_key is not None and self._session_registered:
                    mark_model_session_inactive(self._model_key)
                    self._session_registered = False
                logger.info("SigLIP2Text model session closed.")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
