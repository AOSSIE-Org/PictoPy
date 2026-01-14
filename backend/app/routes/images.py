from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import (
    db_get_all_images,
    db_toggle_image_favourite_status,
    db_get_image_by_id,
    db_delete_images_by_ids,
    db_add_to_deleted_images,
)
from app.schemas.images import ErrorResponse, DeleteImageResponse
from app.utils.images import image_util_parse_metadata, image_util_delete_image_files
from pydantic import BaseModel
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


@router.delete(
    "/{image_id}",
    response_model=DeleteImageResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_image(image_id: str):
    """
    Explicitly delete an image from the library.
    Steps:
    1. Fetch image record from DB.
    2. Add to 'deleted_images' tombstone (prevents re-sync).
    3. Delete physical files (original + thumbnail).
    4. Delete DB record (triggers cascaded delete for tags/metadata).
    """
    try:
        logger.info(f"Image deletion requested for ID: {image_id}")

        # 1. Fetch image record
        image = db_get_image_by_id(image_id)
        if not image:
            logger.warning(f"Image deletion failed: ID {image_id} not found")
            raise HTTPException(status_code=404, detail="Image not found")

        original_path = image.get("path")

        # 2. Add to tombstone
        db_add_to_deleted_images(original_path)

        # 3. Delete files
        # We do this before DB deletion to have the paths available,
        # but if this fails, we still proceed with DB cleanup to keep it consistent.
        image_util_delete_image_files(image)

        # 4. Delete DB record
        # This will trigger ON DELETE CASCADE for faces, album_images, image_classes
        db_delete_images_by_ids([image_id])

        logger.info(f"Successfully deleted image {image_id} and path {original_path}")

        return DeleteImageResponse(
            success=True,
            message="Image deleted successfully",
            data=image_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Failed to delete image: {str(e)}",
            ).model_dump(),
        )
