from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.logging.setup_logging import get_logger
from app.database.semantic_search import (
    db_get_missing_embeddings_image_ids,
    db_upsert_embedding,
    db_get_all_embeddings
)
from app.database.images import db_get_all_images
from app.utils.semantic_search import generate_clip_embedding, search_images
from app.routes.images import ImageData
from app.utils.images import image_util_parse_metadata

logger = get_logger(__name__)
router = APIRouter()

# Global indexing status
indexing_status = {
    "is_active": False,
    "current": 0,
    "total": 0,
    "error": None
}

class SearchResponse(ImageData):
    score: float

def process_indexing_task():
    """Background task to index images."""
    global indexing_status
    indexing_status["is_active"] = True
    indexing_status["error"] = None
    logger.info("Starting background indexing task...")
    
    try:
        # 1. Get images that need indexing
        missing_ids = db_get_missing_embeddings_image_ids()
        total = len(missing_ids)
        indexing_status["total"] = total
        indexing_status["current"] = 0
        
        if not missing_ids:
            logger.info("No images to index.")
            indexing_status["is_active"] = False
            return

        # 2. Get image paths for these IDs
        all_images = db_get_all_images()
        image_map = {img['id']: img['path'] for img in all_images}
        
        count = 0
        
        for image_id in missing_ids:
            if image_id not in image_map:
                continue
                
            path = image_map[image_id]
            try:
                embedding = generate_clip_embedding(path)
                db_upsert_embedding(image_id, embedding)
                count += 1
                indexing_status["current"] = count
                if count % 10 == 0:
                    logger.info(f"Indexed {count}/{total} images...")
            except Exception as e:
                logger.error(f"Failed to index {path}: {e}")
                continue
                
        logger.info(f"Indexing completed. Processed {count} images.")
    except Exception as e:
        logger.error(f"Indexing task failed: {e}")
        indexing_status["error"] = str(e)
    finally:
        indexing_status["is_active"] = False

@router.get("/status")
def get_status():
    """Get current indexing status."""
    return indexing_status

@router.post("/index")
async def trigger_indexing(background_tasks: BackgroundTasks):
    """Trigger background indexing of images."""
    background_tasks.add_task(process_indexing_task)
    return {"message": "Indexing started in background"}

@router.get("/search", response_model=List[SearchResponse])
async def search(q: str):
    """Search images by text query."""
    if not q:
        return []

    try:
        # Load all embeddings (in production, use a vector DB or cache this)
        embeddings = db_get_all_embeddings()
        
        results = search_images(q, embeddings)
        
        # Enrich with image details
        # Get all images again... caching needed for perf, but okay for MVP
        all_images = db_get_all_images()
        image_details_map = {img['id']: img for img in all_images}
        
        response = []
        for result in results:
            img_id = result['image_id']
            if img_id in image_details_map:
                details = image_details_map[img_id]
                details = image_details_map[img_id]
                response.append(SearchResponse(
                    id=details['id'],
                    path=details['path'],
                    folder_id=str(details['folder_id']),
                    thumbnailPath=details['thumbnailPath'],
                    metadata=image_util_parse_metadata(details['metadata']),
                    isTagged=details['isTagged'],
                    isFavourite=details.get('isFavourite', False),
                    tags=details.get('tags'),
                    score=result['score']
                ))
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        # Return error details to help debugging
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
