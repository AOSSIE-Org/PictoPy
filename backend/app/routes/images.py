from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse
from app.utils.images import image_util_parse_metadata
from app.utils.duplicate_detection import get_duplicate_groups_with_scores
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


# Duplicate Detection Models
class DuplicateImageInfo(BaseModel):
    id: str
    path: str
    thumbnailPath: str
    sharpness_score: float
    exposure_score: float
    overall_score: float
    is_best_shot: bool


class DuplicateGroup(BaseModel):
    group_id: int
    image_count: int
    best_shot_id: str
    images: List[DuplicateImageInfo]


class GetDuplicatesResponse(BaseModel):
    success: bool
    message: str
    data: List[DuplicateGroup]


@router.get(
    "/duplicates",
    response_model=GetDuplicatesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_duplicate_images(
    similarity_threshold: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum hash distance to consider images as duplicates (lower = stricter, default 10)"
    )
):
    """
    Find duplicate/similar images and suggest the best shot from each group.
    
    This endpoint analyzes all images in the library to find groups of similar images
    (e.g., multiple shots of the same scene). For each group, it calculates quality
    scores based on sharpness and exposure, and suggests the "best shot".
    
    Quality Metrics:
    - Sharpness: Measured using Laplacian variance (higher = less blur)
    - Exposure: Analyzes histogram for proper brightness and contrast
    - Overall: Weighted combination (60% sharpness, 40% exposure)
    
    Args:
        similarity_threshold: Hash distance threshold (1-50, default 10)
            - Lower values = stricter matching (fewer false positives)
            - Higher values = looser matching (may group different images)
            - Recommended: 10 for ~96% similarity
    
    Returns:
        List of duplicate groups with quality scores and best shot recommendation
    """
    try:
        # Get all images from database
        images = db_get_all_images()
        
        if not images:
            return GetDuplicatesResponse(
                success=True,
                message="No images found in library",
                data=[]
            )
        
        # Prepare image data for duplicate detection
        image_data = [
            {
                'id': img['id'],
                'path': img['path'],
                'thumbnailPath': img.get('thumbnailPath', '')
            }
            for img in images
        ]
        
        # Find duplicate groups with quality scores
        duplicate_groups = get_duplicate_groups_with_scores(
            image_data,
            similarity_threshold=similarity_threshold
        )
        
        # Convert to response format
        response_data = [
            DuplicateGroup(
                group_id=group['group_id'],
                image_count=group['image_count'],
                best_shot_id=group['best_shot_id'],
                images=[
                    DuplicateImageInfo(**img_info)
                    for img_info in group['images']
                ]
            )
            for group in duplicate_groups
        ]
        
        total_duplicates = sum(g.image_count for g in response_data)
        
        return GetDuplicatesResponse(
            success=True,
            message=f"Found {len(response_data)} duplicate groups with {total_duplicates} total images",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to find duplicates: {str(e)}",
            ).model_dump(),
        )
