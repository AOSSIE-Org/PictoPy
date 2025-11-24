from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse
from app.utils.images import image_util_parse_metadata
from pydantic import BaseModel
from app.database.images import db_toggle_image_favourite_status
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class MetadataModel(BaseModel):
    name: str
    date_created: Optional[str]
    width: int
    height: int
    file_location: str
    file_size: int
    item_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


class ImageData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


@router.get(
    "/",
    response_model=GetAllImagesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_images(
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status")
):
    """Get all images from the database."""
    try:
        # Get all images with tags from database (single query with optional filter)
        images = db_get_all_images(tagged=tagged)

        # Convert to response format
        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image_util_parse_metadata(image["metadata"]),
                isTagged=image["isTagged"],
                isFavourite=image.get("isFavourite", False),
                tags=image["tags"],
            )
            for image in images
        ]

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} images",
            data=image_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images: {str(e)}",
            ).model_dump(),
        )


# adding add to favourite and remove from favourite routes


class ToggleFavouriteRequest(BaseModel):
    image_id: str


@router.post("/toggle-favourite")
def toggle_favourite(req: ToggleFavouriteRequest):
    image_id = req.image_id
    try:
        success = db_toggle_image_favourite_status(image_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Image not found or failed to toggle"
            )
        # Fetch updated status to return
        image = next(
            (img for img in db_get_all_images() if img["id"] == image_id), None
        )
        return {
            "success": True,
            "image_id": image_id,
            "isFavourite": image.get("isFavourite", False),
        }

    except Exception as e:
        logger.error(f"error in /toggle-favourite route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class ImageInfoResponse(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None


# Batch Operations
from app.schemas.batch import (
    BatchDeleteRequest,
    BatchTagRequest,
    BatchMoveRequest,
    BatchOperationResponse
)
from app.database.images import db_delete_image, db_add_tags_to_image


@router.delete("/batch-delete", response_model=BatchOperationResponse)
def batch_delete_images(request: BatchDeleteRequest):
    """Delete multiple images"""
    processed = 0
    failed = 0
    errors = []
    
    for image_id in request.image_ids:
        try:
            success = db_delete_image(image_id)
            if success:
                processed += 1
            else:
                failed += 1
                errors.append(f"Image {image_id} not found")
        except Exception as e:
            failed += 1
            errors.append(f"Failed to delete {image_id}: {str(e)}")
            logger.error(f"Error deleting image {image_id}: {e}")
    
    return BatchOperationResponse(
        success=failed == 0,
        processed=processed,
        failed=failed,
        errors=errors
    )


@router.post("/batch-tag", response_model=BatchOperationResponse)
def batch_tag_images(request: BatchTagRequest):
    """Add tags to multiple images"""
    processed = 0
    failed = 0
    errors = []
    
    for image_id in request.image_ids:
        try:
            success = db_add_tags_to_image(image_id, request.tags)
            if success:
                processed += 1
            else:
                failed += 1
                errors.append(f"Image {image_id} not found")
        except Exception as e:
            failed += 1
            errors.append(f"Failed to tag {image_id}: {str(e)}")
            logger.error(f"Error tagging image {image_id}: {e}")
    
    return BatchOperationResponse(
        success=failed == 0,
        processed=processed,
        failed=failed,
        errors=errors
    )


@router.post("/batch-move", response_model=BatchOperationResponse)
def batch_move_to_album(request: BatchMoveRequest):
    """Move multiple images to an album"""
    processed = 0
    failed = 0
    errors = []
    
    # TODO: Implement album functionality
    for image_id in request.image_ids:
        try:
            # Placeholder for album move functionality
            # success = db_add_image_to_album(image_id, request.album_id)
            processed += 1
        except Exception as e:
            failed += 1
            errors.append(f"Failed to move {image_id}: {str(e)}")
            logger.error(f"Error moving image {image_id}: {e}")
    
    return BatchOperationResponse(
        success=failed == 0,
        processed=processed,
        failed=failed,
        errors=errors
    )
