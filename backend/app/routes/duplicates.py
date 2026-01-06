from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.database.images import db_get_all_images_with_phash, db_delete_images_by_ids, db_get_images_by_ids
from app.utils.duplicate_detector import identify_best_shot, group_similar_images
from app.logging.setup_logging import get_logger
import os

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_duplicates():
    """
    Get groups of duplicate images.
    Returns a list of groups, where each group contains:
    - images: List of image objects
    - best_shot_id: ID of the best shot
    """
    try:
        # Get all images with pHash
        all_images = db_get_all_images_with_phash()
        
        # Group similar images using Python logic (Hamming distance)
        # Threshold 5 allows for some edits/compression differences
        groups = group_similar_images(all_images, threshold=5)
        
        result = []
        
        for group in groups:
            best_shot = identify_best_shot(group)
            result.append({
                "images": group,
                "best_shot_id": best_shot['id'] if best_shot else None
            })
            
        return result
    except Exception as e:
        logger.error(f"Error getting duplicates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/delete", response_model=Dict[str, int])
async def delete_duplicates(image_ids: List[str] = Body(...)):
    """
    Delete specified duplicate images from DB and filesystem.
    """
    try:
        # Get image paths before deleting from DB
        images = db_get_images_by_ids(image_ids)
        
        # Delete from DB
        if not db_delete_images_by_ids(image_ids):
            raise HTTPException(status_code=500, detail="Failed to delete images from database")
            
        # Delete from filesystem
        deleted_files_count = 0
        for img in images:
            try:
                if os.path.exists(img['path']):
                    os.remove(img['path'])
                    deleted_files_count += 1
                
                # Also delete thumbnail
                if img.get('thumbnailPath') and os.path.exists(img['thumbnailPath']):
                    os.remove(img['thumbnailPath'])
            except Exception as e:
                logger.error(f"Error deleting file {img['path']}: {e}")
                
        return {"deleted_count": len(image_ids), "deleted_files_count": deleted_files_count}
        
    except Exception as e:
        logger.error(f"Error in delete_duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
