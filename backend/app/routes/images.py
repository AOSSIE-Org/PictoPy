from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse
from pydantic import BaseModel
from app.database.images import db_toggle_image_favourite_status
router = APIRouter()


# Response Models
class ImageData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: str
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
def get_all_images():
    """Get all images from the database."""
    try:
        # Get all images with tags from database (single query)
        images = db_get_all_images()

        # Convert to response format
        image_data = [
                ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image["metadata"],
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
        raise HTTPException(status_code=404, detail="Image not found or failed to toggle")
        # Fetch updated status to return
        image = next((img for img in db_get_all_images() if img["id"] == image_id), None)
        return {"success": True, "image_id": image_id, "isFavourite": image.get("isFavourite", False)}

    except Exception as e:
        print(f"Toggle favourite error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

class ImageInfoResponse(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: str
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None

@router.get("/info/{image_id}", response_model=ImageInfoResponse)
def get_image_info(image_id: str):
    # 1. Fetch all images
    images = db_get_all_images()
    image = next((img for img in images if img["id"] == image_id), None)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return ImageInfoResponse(
        id=image["id"],
        path=image["path"],
        folder_id=image["folder_id"],
        thumbnailPath=image["thumbnailPath"],
        metadata=image["metadata"],
        isTagged=image["isTagged"],
        isFavourite=image.get("isFavourite", False),
        tags=image.get("tags", [])
    )