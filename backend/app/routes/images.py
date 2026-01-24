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


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


class PaginatedImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]
    pagination: PaginationInfo


@router.get(
    "/",
    response_model=None,
    responses={500: {"model": ErrorResponse}},
)
def get_all_images(
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Number of images per page (max 100)"
    ),
):
    """
    Get all images from the database.

    - If `page` and `limit` are provided, returns paginated results.
    - If `page` and `limit` are not provided, returns all images (backward compatible).
    """
    try:
        # Get images with optional pagination
        result = db_get_all_images(tagged=tagged, page=page, limit=limit)

        # Check if paginated result
        if page is not None and limit is not None:
            images = result["images"]
            pagination = result["pagination"]

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

            return PaginatedImagesResponse(
                success=True,
                message=f"Successfully retrieved {len(image_data)} images (page {pagination['page']} of {pagination['total_pages']})",
                data=image_data,
                pagination=PaginationInfo(**pagination),
            )
        else:
            # Non-paginated response (backward compatible)
            images = result

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
