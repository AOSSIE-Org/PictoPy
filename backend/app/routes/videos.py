from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
import json

from app.database.videos import (
    db_get_all_videos,
    db_get_video_by_id,
    db_toggle_video_favourite_status,
    db_get_favourite_videos,
)
from app.schemas.videos import (
    VideoData,
    VideoMetadata,
    GetAllVideosResponse,
    ToggleVideoFavouriteRequest,
    ToggleVideoFavouriteResponse,
    ErrorResponse,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


def _parse_video_metadata(metadata_str: Optional[str]) -> Optional[VideoMetadata]:
    """Parse video metadata from JSON string."""
    if not metadata_str:
        return None
    try:
        metadata_dict = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
        return VideoMetadata(**metadata_dict)
    except Exception as e:
        logger.warning(f"Failed to parse video metadata: {e}")
        return None


@router.get(
    "/",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_videos():
    """
    Get all videos from the database.
    
    Returns a list of all videos with their metadata.
    """
    try:
        videos_data = db_get_all_videos()
        
        videos = []
        for video in videos_data:
            metadata = _parse_video_metadata(video.get("metadata"))
            
            videos.append(
                VideoData(
                    id=video["id"],
                    path=video["path"],
                    folder_id=str(video["folder_id"]),
                    thumbnailPath=video["thumbnailPath"] or "",
                    duration=video.get("duration"),
                    width=video.get("width"),
                    height=video.get("height"),
                    isFavourite=bool(video.get("isFavourite", False)),
                    metadata=metadata,
                )
            )
        
        return GetAllVideosResponse(
            success=True,
            message=f"Successfully retrieved {len(videos)} videos",
            data=videos,
        )
        
    except Exception as e:
        logger.error(f"Error getting all videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve videos: {str(e)}"
            ).model_dump()
        )


@router.get(
    "/favourites",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_favourite_videos():
    """
    Get all favourite videos from the database.
    """
    try:
        videos_data = db_get_favourite_videos()
        
        videos = []
        for video in videos_data:
            metadata = _parse_video_metadata(video.get("metadata"))
            
            videos.append(
                VideoData(
                    id=video["id"],
                    path=video["path"],
                    folder_id=str(video["folder_id"]),
                    thumbnailPath=video["thumbnailPath"] or "",
                    duration=video.get("duration"),
                    width=video.get("width"),
                    height=video.get("height"),
                    isFavourite=bool(video.get("isFavourite", False)),
                    metadata=metadata,
                )
            )
        
        return GetAllVideosResponse(
            success=True,
            message=f"Successfully retrieved {len(videos)} favourite videos",
            data=videos,
        )
        
    except Exception as e:
        logger.error(f"Error getting favourite videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve favourite videos: {str(e)}"
            ).model_dump()
        )


@router.get(
    "/{video_id}",
    response_model=VideoData,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_video(video_id: str):
    """
    Get a single video by ID.
    """
    try:
        video = db_get_video_by_id(video_id)
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not found",
                    message=f"Video with ID {video_id} not found"
                ).model_dump()
            )
        
        metadata = _parse_video_metadata(video.get("metadata"))
        
        return VideoData(
            id=video["id"],
            path=video["path"],
            folder_id=str(video["folder_id"]),
            thumbnailPath=video["thumbnailPath"] or "",
            duration=video.get("duration"),
            width=video.get("width"),
            height=video.get("height"),
            isFavourite=bool(video.get("isFavourite", False)),
            metadata=metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve video: {str(e)}"
            ).model_dump()
        )


@router.post(
    "/toggle-favourite",
    response_model=ToggleVideoFavouriteResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def toggle_video_favourite(request: ToggleVideoFavouriteRequest):
    """
    Toggle the favourite status of a video.
    """
    try:
        # Check if video exists
        video = db_get_video_by_id(request.video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not found",
                    message=f"Video with ID {request.video_id} not found"
                ).model_dump()
            )
        
        success = db_toggle_video_favourite_status(request.video_id)
        
        if success:
            return ToggleVideoFavouriteResponse(
                success=True,
                message="Video favourite status toggled successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    error="Update failed",
                    message="Failed to toggle video favourite status"
                ).model_dump()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling video favourite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to toggle favourite status: {str(e)}"
            ).model_dump()
        )
