from pydantic import BaseModel
from typing import Optional, List, Mapping, Any


class VideoMetadata(BaseModel):
    name: str
    date_created: Optional[str] = None
    width: int
    height: int
    duration: float
    file_location: str
    file_size: int
    item_type: str


class VideoData(BaseModel):
    id: str
    path: str
    folder_id: Optional[str] = None
    thumbnailPath: Optional[str] = None
    metadata: Mapping[str, Any] | VideoMetadata


class GetAllVideosResponse(BaseModel):
    success: bool
    message: str
    data: List[VideoData]


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
