from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import (
    db_get_all_images,
    db_soft_delete_images,
    db_restore_images,
    db_get_deleted_images,
    db_permanently_delete_images,
    db_permanently_delete_old_images,
)
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
    is_deleted: Optional[bool] = False
    deleted_at: Optional[str] = None
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
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status"),
    include_deleted: Optional[bool] = Query(
        False, description="Include soft deleted images"
    ),
):
    """Get all images from the database."""
    try:
        # Get all images with tags from database (single query with optional filter)
        images = db_get_all_images(tagged=tagged, include_deleted=include_deleted)

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
                is_deleted=image.get("is_deleted", False),
                deleted_at=image.get("deleted_at"),
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


class DeleteRequest(BaseModel):
    image_id: str


@router.post("/delete")
def delete_image(req: DeleteRequest):
    image_id = req.image_id
    try:
        success = db_soft_delete_images([image_id])
        if not success:
            raise HTTPException(
                status_code=404, detail="Image not found or failed to delete"
            )
        return {
            "success": True,
            "image_id": image_id,
            "is_deleted": True,
        }

    except Exception as e:
        logger.error(f"error in /delete route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class ImageInfoResponse(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    is_deleted: Optional[bool] = False
    deleted_at: Optional[str] = None
    tags: Optional[List[str]] = None


# Soft Delete Endpoints


class SoftDeleteRequest(BaseModel):
    image_ids: List[str]


class SoftDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int


@router.post("/soft-delete", response_model=SoftDeleteResponse)
def soft_delete_images(req: SoftDeleteRequest):
    """Soft delete multiple images."""
    try:
        success = db_soft_delete_images(req.image_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to soft delete images")

        return SoftDeleteResponse(
            success=True,
            message=f"Successfully soft deleted {len(req.image_ids)} images",
            deleted_count=len(req.image_ids),
        )
    except Exception as e:
        logger.error(f"Error in /soft-delete route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class RestoreRequest(BaseModel):
    image_ids: List[str]


class RestoreResponse(BaseModel):
    success: bool
    message: str
    restored_count: int


@router.post("/restore", response_model=RestoreResponse)
def restore_images(req: RestoreRequest):
    """Restore multiple soft deleted images."""
    try:
        success = db_restore_images(req.image_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restore images")

        return RestoreResponse(
            success=True,
            message=f"Successfully restored {len(req.image_ids)} images",
            restored_count=len(req.image_ids),
        )
    except Exception as e:
        logger.error(f"Error in /restore route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class GetDeletedImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


@router.get("/deleted", response_model=GetDeletedImagesResponse)
def get_deleted_images():
    """Get all soft deleted images."""
    try:
        images = db_get_deleted_images()

        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image_util_parse_metadata(image["metadata"]),
                isTagged=image["isTagged"],
                isFavourite=image.get("isFavourite", False),
                is_deleted=True,
                deleted_at=image["deleted_at"],
                tags=None,  # Deleted images don't show tags
            )
            for image in images
        ]

        return GetDeletedImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} deleted images",
            data=image_data,
        )
    except Exception as e:
        logger.error(f"Error in /deleted route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class PermanentDeleteRequest(BaseModel):
    image_ids: List[str]


class PermanentDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int


@router.post("/permanent-delete", response_model=PermanentDeleteResponse)
def permanent_delete_images(req: PermanentDeleteRequest):
    """Permanently delete images from history."""
    try:
        success = db_permanently_delete_images(req.image_ids)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to permanently delete images"
            )

        return PermanentDeleteResponse(
            success=True,
            message=f"Successfully permanently deleted {len(req.image_ids)} images",
            deleted_count=len(req.image_ids),
        )
    except Exception as e:
        logger.error(f"Error in /permanent-delete route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class CleanupOldImagesResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int


@router.post("/cleanup", response_model=CleanupOldImagesResponse)
def cleanup_old_images(
    days: int = Query(30, description="Days after which to permanently delete")
):
    """Permanently delete images that have been soft deleted for more than the specified days."""
    try:
        deleted_count = db_permanently_delete_old_images(days=days)

        return CleanupOldImagesResponse(
            success=True,
            message=f"Successfully cleaned up {deleted_count} old images",
            deleted_count=deleted_count,
        )
    except Exception as e:
        logger.error(f"Error in /cleanup route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
