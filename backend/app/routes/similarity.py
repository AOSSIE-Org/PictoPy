
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.utils.similarity import SimilarityEngine
from app.database.similarity import db_save_embedding, db_get_all_embeddings
from app.database.images import db_get_all_images # Assuming this exists or similar
import numpy as np
from scipy.spatial.distance import cdist
from app.logging.setup_logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

similarity_engine = SimilarityEngine()

def process_all_images():
    """Background task to generate embeddings for all images."""
    logger.info("Starting background embedding generation...")
    # NOTE: In a real integration, we'd fetch all images from the images table.
    # For now, we assume we can iterate over a known list or scan.
    # mocking db_get_all_images call for safety if not exists
    try:
        from app.database.images import db_get_all_images
        images = db_get_all_images() # returns list of dicts or objects
    except ImportError:
        logger.warning("Could not import db_get_all_images, skipping scan.")
        return

    count = 0
    for img in images:
        path = img['path'] # adjust key based on schema
        embedding = similarity_engine.compute_embedding(path)
        if embedding is not None:
            db_save_embedding(path, embedding)
            count += 1
    logger.info(f"Embedding generation complete. Processed {count} images.")

@router.post("/scan")
async def scan_library(background_tasks: BackgroundTasks):
    """Trigger background scan to compute embeddings."""
    background_tasks.add_task(process_all_images)
    return {"message": "Similarity scan started in background."}

@router.get("/duplicates")
async def find_duplicates(threshold: float = 0.95):
    """Find duplicate images based on cosine similarity."""
    embeddings_map = db_get_all_embeddings()
    if not embeddings_map:
        return {"duplicates": []}
    
    paths = list(embeddings_map.keys())
    matrix = np.stack(list(embeddings_map.values()))
    
    # Compute potential duplicates
    # This is O(N^2), feasible for small collections < 5k images locally.
    # For optimization, FAISS or similar could be used.
    
    duplicates = []
    visited = set()
    
    # Dot product for normalized vectors is cosine similarity
    sim_matrix = np.dot(matrix, matrix.T)
    
    indices = np.where(sim_matrix > threshold)
    
    # Group them
    for i, j in zip(*indices):
        if i != j and i not in visited and j not in visited:
            # We found a pair (or more). Simple pair logic for now.
            duplicates.append([paths[i], paths[j]])
            visited.add(i)
            visited.add(j)
            
    return {"duplicates": duplicates, "count": len(duplicates)}

@router.get("/search/{target_path:path}")
async def search_similar(target_path: str, limit: int = 10):
    """Find images similar to the target path."""
    embeddings_map = db_get_all_embeddings()
    
    if target_path not in embeddings_map:
        # compute on the fly ?
        vec = similarity_engine.compute_embedding(target_path)
        if vec is None:
             raise HTTPException(status_code=404, detail="Image not processed or invalid")
    else:
        vec = embeddings_map[target_path]
        
    paths = list(embeddings_map.keys())
    matrix = np.stack(list(embeddings_map.values()))
    
    scores = np.dot(matrix, vec)
    top_indices = np.argsort(scores)[::-1][:limit]
    
    results = []
    for idx in top_indices:
        if paths[idx] != target_path:
             results.append({"path": paths[idx], "score": float(scores[idx])})
             
    return results
