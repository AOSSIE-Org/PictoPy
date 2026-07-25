from __future__ import annotations
import numpy as np
import onnxruntime

from app.models.ONNXSessionBase import ONNXSessionBase


class SigLIP2Text(ONNXSessionBase):
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.input_ids_name: str | None = None
        self.attention_mask_name: str | None = None
        self.output_tensor_name: str | None = None

    def _clear_tensor_names(self) -> None:
        self.input_ids_name = None
        self.attention_mask_name = None
        self.output_tensor_name = None

    def get_session(self) -> tuple[onnxruntime.InferenceSession, str, str, str]:
        # Snapshot into locals up front and use only the locals from here on --
        # never re-read self.* after this point (see ONNXSessionBase docstring).
        session = self._session
        input_ids_name = self.input_ids_name
        attention_mask_name = self.attention_mask_name
        output_tensor_name = self.output_tensor_name
        if session is not None:
            if None in (input_ids_name, attention_mask_name, output_tensor_name):
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )
            return session, input_ids_name, attention_mask_name, output_tensor_name

        with self._lock:
            if self._session is None:
                self._session = self._create_session()

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

            # Re-snapshot into locals while still holding the lock, then
            # return those locals -- not self.* -- after the lock releases.
            session = self._session
            input_ids_name = self.input_ids_name
            attention_mask_name = self.attention_mask_name
            output_tensor_name = self.output_tensor_name
            if session is None or None in (
                input_ids_name,
                attention_mask_name,
                output_tensor_name,
            ):
                raise RuntimeError(
                    f"Model session for '{self._model_key}' was closed while "
                    "get_session() was executing."
                )

        return session, input_ids_name, attention_mask_name, output_tensor_name

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
