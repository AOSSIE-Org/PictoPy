from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.logging.setup_logging import get_logger
from app.database.images import db_get_image_by_id


logger = get_logger(__name__)
router = APIRouter()


class ShareRequest(BaseModel):
    image_id: str  # Changed to str since your IDs are TEXT in database


class ShareData(BaseModel):
    success: bool
    message: str


class ShareResponse(BaseModel):
    data: ShareData
    success: bool
    message: str


@router.post("", response_model=ShareResponse)
def share_image(req: ShareRequest):
    """
    Log image share action using image ID (frontend handles actual sharing).
    Security: Uses database lookup instead of trusting client-supplied paths.
    """
    try:
        # Get image from database by ID
        image = db_get_image_by_id(req.image_id)
        
        if not image:
            logger.error(f"Image not found with ID: {req.image_id}")
            raise HTTPException(status_code=404, detail={"message": "Image not found"})
        
        # Get the validated path from database
        img_path = image.get('path') or image.get('thumbnailPath')
        
        if not img_path:
            logger.error(f"No path found for image ID: {req.image_id}")
            raise HTTPException(status_code=404, detail={"message": "Image path not found"})
        
        # Verify file still exists on filesystem
        if not os.path.exists(img_path):
            logger.warning(f"Image file not found on disk: {img_path} (ID: {req.image_id})")
            # Don't fail - file might have been moved, just log the warning
        
        # Validate it's an image file
        valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"}
        file_ext = os.path.splitext(img_path)[1].lower()
        
        if file_ext not in valid_extensions:
            logger.error(f"Invalid image file type: {file_ext} (ID: {req.image_id})")
            raise HTTPException(status_code=400, detail={"message": "Invalid image file type"})
        
        # Log the share action
        logger.info(f"Share requested for image ID {req.image_id}: {img_path}")

        return ShareResponse(
            data=ShareData(
                success=True, 
                message="Share logged successfully"
            ),
            success=True,
            message="Share request processed"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing share request: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})