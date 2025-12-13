from pydantic import BaseModel
from typing import List, Optional, Any


class VideoMetadata(BaseModel):
    """Video metadata model."""
    name: str
    file_location: str
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    codec: Optional[str] = None
    date_created: Optional[str] = None


class VideoData(BaseModel):
    """Video data model for API responses."""
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    isFavourite: bool = False
    metadata: Optional[VideoMetadata] = None


class GetAllVideosResponse(BaseModel):
    """Response model for getting all videos."""
    success: bool
    message: str
    data: List[VideoData]


class ToggleVideoFavouriteRequest(BaseModel):
    """Request model for toggling video favourite status."""
    video_id: str


class ToggleVideoFavouriteResponse(BaseModel):
    """Response model for toggling video favourite status."""
    success: bool
    message: str


# Import shared ErrorResponse from common module
from app.schemas.common import ErrorResponse
