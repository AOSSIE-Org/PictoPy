from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str


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
    """One video as every route returns it: the videos listing, semantic search
    and the face cluster surfaces all hand the frontend this shape."""

    id: str
    path: str
    folder_id: str
    thumbnailPath: Optional[str]
    metadata: VideoMetadataModel
    isFavourite: bool
    favouritedAt: Optional[str] = None
    tags: Optional[List[str]] = None
