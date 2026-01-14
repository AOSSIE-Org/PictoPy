from sentence_transformers import SentenceTransformer
from PIL import Image
import numpy as np
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Global variable to hold the model singleton
import threading
_model = None
_model_lock = threading.Lock()

def get_model():
    """Load the CLIP model lazily and safely."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Loading CLIP model 'sentence-transformers/clip-ViT-B-32'...")
                try:
                    _model = SentenceTransformer('sentence-transformers/clip-ViT-B-32')
                    logger.info("CLIP model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load CLIP model: {e}")
                    raise e
    return _model

def generate_clip_embedding(image_path: str) -> np.ndarray:
    """Generate normalized embedding for an image."""
    model = get_model()
    try:
        with Image.open(image_path) as image:
            # SentenceTransformer handles preprocessing
            embedding = model.encode(image)
            return embedding
    except Exception as e:
        logger.error(f"Error generating embedding for {image_path}: {e}")
        raise e

def generate_text_embedding(text: str) -> np.ndarray:
    """Generate normalized embedding for a text query."""
    model = get_model()
    try:
        embedding = model.encode(text)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding for text '{text}': {e}")
        raise e

def search_images(query_text: str, embeddings_dict: dict, limit: int = 50) -> list:
    """
    Search images using cosine similarity.
    embeddings_dict: {image_id: numpy_array}
    """
    if not embeddings_dict:
        return []

    # 1. Encode query
    query_embedding = generate_text_embedding(query_text)
    
    # 2. Prepare data for vectorized calculation
    image_ids = list(embeddings_dict.keys())
    # Stack embeddings into a matrix (N, D)
    embeddings_matrix = np.vstack([embeddings_dict[id] for id in image_ids])
    
    # 3. Compute Cosine Similarity
    # sentence-transformers embeddings are usually already normalized? 
    # By default encode(normalize_embeddings=False). 
    # But let's assume we want to be safe and use cosine similarity explicitly.
    # Cosine Similarity = (A . B) / (||A|| * ||B||)
    
    # Calculate norms
    query_norm = np.linalg.norm(query_embedding)
    matrix_norms = np.linalg.norm(embeddings_matrix, axis=1)
    
    # Avoid division by zero
    matrix_norms[matrix_norms == 0] = 1e-10
    if query_norm == 0:
        query_norm = 1e-10
        
    # Dot product
    dot_products = np.dot(embeddings_matrix, query_embedding)
    
    # Similarity scores
    scores = dot_products / (matrix_norms * query_norm)
    
    # 4. Sort and return top N
    # argsort returns indices that would sort the array, in ascending order
    # we want descending order
    top_indices = np.argsort(scores)[::-1][:limit]
    
    results = []
    for idx in top_indices:
        results.append({
            "image_id": image_ids[idx],
            "score": float(scores[idx])
        })
        
    return results
