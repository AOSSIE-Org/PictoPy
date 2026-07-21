from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database.videos import (
    db_get_all_videos,
    db_toggle_video_favourite_status,
    db_get_video_by_id,
)
from app.schemas.videos import ErrorResponse
from app.utils.images import image_util_parse_metadata
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class VideoMetadataModel(BaseModel):
    name: str
    date_created: Optional[str]
    width: int
    height: int
    duration: Optional[float] = None
    fps: Optional[float] = None
    file_location: str
    file_size: int
    item_type: str


class VideoData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: Optional[str]
    metadata: VideoMetadataModel
    isFavourite: bool
    tags: Optional[List[str]] = None


class GetAllVideosResponse(BaseModel):
    success: bool
    message: str
    data: List[VideoData]


@router.get(
    "/",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_videos():
    """Get all videos from the database."""
    try:
        videos = db_get_all_videos()

        video_data = [
            VideoData(
                id=video["id"],
                path=video["path"],
                folder_id=video["folder_id"],
                thumbnailPath=video["thumbnailPath"],
                metadata=image_util_parse_metadata(video["metadata"]),
                isFavourite=video.get("isFavourite", False),
                tags=video["tags"],
            )
            for video in videos
        ]

        return GetAllVideosResponse(
            success=True,
            message=f"Successfully retrieved {len(video_data)} videos",
            data=video_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve videos: {str(e)}",
            ).model_dump(),
        )


class ToggleFavouriteRequest(BaseModel):
    video_id: str


@router.post("/toggle-favourite")
def toggle_favourite(req: ToggleFavouriteRequest):
    """
    Toggle the favorite status of a video.
    """
    video_id = req.video_id
    try:
        success = db_toggle_video_favourite_status(video_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or failed to toggle",
            )
        # Fetch updated status to return
        video = db_get_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found after toggle",
            )
        return {
            "success": True,
            "video_id": video_id,
            "isFavourite": video.get("isFavourite", False),
        }
    except HTTPException:
        raise  # Re-raise HTTPExceptions to preserve status codes
    except Exception as e:
        logger.error(f"error in /toggle-favourite route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )
