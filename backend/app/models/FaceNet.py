# app/facenet/FaceNet.py

import onnxruntime
from app.utils.FaceNet import FaceNet_util_normalize_embedding
from app.utils.ONNX import ONNX_util_get_execution_providers
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class FaceNet:
    def __init__(self, model_path):
        self.session = onnxruntime.InferenceSession(model_path, providers=ONNX_util_get_execution_providers())
        self.input_tensor_name = self.session.get_inputs()[0].name
        self.output_tensor_name = self.session.get_outputs()[0].name

    def get_embedding(self, preprocessed_image):
        result = self.session.run([self.output_tensor_name], {self.input_tensor_name: preprocessed_image})[0]
        embedding = result[0]
        return FaceNet_util_normalize_embedding(embedding)

    def close(self):
        del self.session
        logger.info("FaceNet model session closed.")
