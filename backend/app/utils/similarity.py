
import os
import numpy as np
import onnxruntime as ort
from PIL import Image
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

class SimilarityEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimilarityEngine, cls).__new__(cls)
            cls._instance.model_path = os.path.join(os.path.dirname(__file__), "mobilenetv2-7.onnx")
            cls._instance.session = None
        return cls._instance

    def load_model(self):
        """Loads the ONNX model if not already loaded."""
        if self.session is None:
            if not os.path.exists(self.model_path):
                logger.error(f"MobileNetV2 model not found at {self.model_path}")
                # In a real scenario, we might download it here
                return False
            try:
                # Set providers to CPU for compatibility
                self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                logger.info("MobileNetV2 model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load MobileNetV2 model: {e}")
                return False
        return True

    def preprocess_image(self, image_path):
        """Preprocesses image for MobileNetV2 (224x224, normalized)."""
        try:
            img = Image.open(image_path).convert('RGB')
            img = img.resize((224, 224))
            img_data = np.array(img).astype('float32')
            
            # Normalize: (val - mean) / std. MobileNet expect [0,1] or standard normalization
            # MobileNetV2 generic expectation: scale to [0, 1], then normalize
            img_data /= 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype='float32')
            std = np.array([0.229, 0.224, 0.225], dtype='float32')
            img_data = (img_data - mean) / std
            
            # Transpose to (1, 3, 224, 224)
            img_data = img_data.transpose(2, 0, 1)
            img_data = np.expand_dims(img_data, axis=0)
            return img_data
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None

    def compute_embedding(self, image_path):
        """Computes the 1280-d embedding for an image."""
        if not self.load_model():
            return None
        
        input_data = self.preprocess_image(image_path)
        if input_data is None:
            return None
        
        try:
            inputs = {self.session.get_inputs()[0].name: input_data}
            outputs = self.session.run(None, inputs)
            # MobileNetV2 (without classifier) output usually (1, 1280, 7, 7) or similar.
            # We want a global pool. For generic MobileNetV2-7: output is 'output'
            # If standard ImageNet model, last layer before classifier.
            # Assuming the output is the feature vector or we pool it.
            
            # MobileNetV2 output is (1, 1280, 7, 7). We perform Global Average Pooling.
            output = outputs[0]
            if len(output.shape) == 4:
                output = np.mean(output, axis=(2, 3)) # (1, 1280)
            
            embedding = output.flatten()
            
            return embedding / np.linalg.norm(embedding) # Normalize for Cosine Sim
        except Exception as e:
            logger.error(f"Inference error for {image_path}: {e}")
            return None
