import os
import threading
import onnxruntime
from app.models.model_registry import MODEL_REGISTRY
from app.utils.FaceNet import FaceNet_util_normalize_embedding
from app.utils.ONNX import ONNX_util_get_execution_providers
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class FaceNet:
    def __init__(self, model_path):
        self.model_path = model_path
        self._session: onnxruntime.InferenceSession | None = None
        self.input_tensor_name: str | None = None
        self.output_tensor_name: str | None = None
        self._lock = threading.Lock()

    def get_session(self) -> onnxruntime.InferenceSession:
        # Fast path: capture reference before returning so close() on another
        # thread between the check and the return cannot cause a None return.
        session = self._session
        if session is not None:
            return session

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
                self.input_tensor_name = self._session.get_inputs()[0].name
                self.output_tensor_name = self._session.get_outputs()[0].name

            # Capture inside the lock before releasing — prevents close() on
            # another thread from nulling _session between lock release and return.
            session = self._session

        return session

    def get_embedding(self, preprocessed_image):
        session = self.get_session()
        result = session.run(
            [self.output_tensor_name], {self.input_tensor_name: preprocessed_image}
        )[0]
        embedding = result[0]
        return FaceNet_util_normalize_embedding(embedding)

    def close(self):
        with self._lock:
            if self._session is not None:
                self._session = None
                self.input_tensor_name = None
                self.output_tensor_name = None
                logger.info("FaceNet model session closed.")
