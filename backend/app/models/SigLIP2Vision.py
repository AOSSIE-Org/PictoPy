from __future__ import annotations
import numpy as np
import onnxruntime

from app.models.ONNXSessionBase import ONNXSessionBase


class SigLIP2Vision(ONNXSessionBase):
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.input_tensor_name: str | None = None
        self.output_tensor_name: str | None = None

    def _clear_tensor_names(self) -> None:
        self.input_tensor_name = None
        self.output_tensor_name = None

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
                self._session = self._create_session()
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
