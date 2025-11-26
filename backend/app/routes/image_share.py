from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.logging.setup_logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


class ShareRequest(BaseModel):
    path: str


class ShareData(BaseModel):
    success: bool
    message: str


class ShareResponse(BaseModel):
    data: ShareData
    success: bool
    message: str


@router.post("/share", response_model=ShareResponse)
def share_image(req: ShareRequest):
    """
    Log image share action (frontend handles actual sharing).
    """
    img_path = req.path

    # Validate file existence
    if not os.path.exists(img_path):
        logger.error(f"Image not found: {img_path}")
        raise HTTPException(status_code=404, detail={"message": "Image not found"})
    
    # Validate it's an image file
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"}
    file_ext = os.path.splitext(img_path)[1].lower()
    
    if file_ext not in valid_extensions:
        logger.error(f"Invalid image file type: {file_ext}")
        raise HTTPException(status_code=400, detail={"message": "Invalid image file type"})
    
    # Just log the share action - don't open anything
    logger.info(f"Image share requested: {img_path}")

    return ShareResponse(
        data=ShareData(success=True, message="Share logged successfully"),
        success=True,
        message="Share request processed"
    )