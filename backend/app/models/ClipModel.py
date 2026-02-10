import torch
from sentence_transformers import SentenceTransformer
from PIL import Image
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

class ClipModel:
    def __init__(self, model_name='clip-ViT-B-32'):
        try:
            logger.info(f"Loading CLIP model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise e

    def get_embedding(self, image_path: str):
        """
        Generates a CLIP embedding for the given image.
        """
        try:
            image = Image.open(image_path)
            embedding = self.model.encode(image)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding for {image_path}: {e}")
            return None

    def get_text_embedding(self, text: str):
        """
        Generates a CLIP embedding for the given text query.
        """
        try:
            embedding = self.model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding for text '{text}': {e}")
            return None
