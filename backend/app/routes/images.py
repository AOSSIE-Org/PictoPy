from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse
from app.config.pagination import (
    MAX_PAGE_SIZE,
    MAX_OFFSET_VALUE,
    MIN_PAGE_SIZE,
)
from pydantic import BaseModel

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
    tags: Optional[List[str]] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@router.get(
    "/",
    response_model=GetAllImagesResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_all_images(
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status"),
    limit: Optional[int] = Query(
        None,
        description="Number of images per page",
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
    ),
    offset: Optional[int] = Query(None, description="Number of images to skip", ge=0),
):
    """
    Retrieve images with optional filtering and pagination.
    
    Returns paginated results with total count metadata.
    """
    try:
        if limit is not None and offset is not None and offset > MAX_OFFSET_VALUE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid offset",
                    message=f"Offset exceeds maximum allowed value ({MAX_OFFSET_VALUE})",
                ).model_dump(),
            )

        result = db_get_all_images(tagged=tagged, limit=limit, offset=offset)
        images = result["images"]
        total_count = result["total"]

        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image["metadata"],
                isTagged=image["isTagged"],
                tags=image["tags"],
            )
            for image in images
        ]

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} of {total_count} images",
            data=image_data,
            total=total_count,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images: {str(e)}",
            ).model_dump(),
        )
