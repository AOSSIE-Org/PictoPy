from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Request Models
class GenerateMemoriesRequest(BaseModel):
    """Request to generate memories from existing photos."""
    force_regenerate: bool = Field(
        default=False,
        description="If True, clear existing memories and regenerate all"
    )


# Response Models
class MemorySummary(BaseModel):
    """Summary of a memory for list view."""
    id: str
    title: str
    memory_type: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_photos: int
    representative_thumbnails: List[str] = []
    created_at: str


class ImageInMemory(BaseModel):
    """Image details within a memory."""
    id: str
    path: str
    thumbnailPath: str
    metadata: dict
    is_representative: bool


class MemoryDetail(BaseModel):
    """Detailed memory with all images."""
    id: str
    title: str
    memory_type: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cover_image_id: Optional[str] = None
    total_photos: int
    created_at: str
    images: List[ImageInMemory]


class GetAllMemoriesResponse(BaseModel):
    """Response for getting all memories."""
    success: bool
    message: str
    data: List[MemorySummary]


class GetMemoryDetailResponse(BaseModel):
    """Response for getting a specific memory."""
    success: bool
    message: str
    data: MemoryDetail


class GenerateMemoriesResponse(BaseModel):
    """Response for memory generation."""
    success: bool
    message: str
    data: dict = Field(
        description="Contains memories_created count and generation stats"
    )


class DeleteMemoryResponse(BaseModel):
    """Response for memory deletion."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    message: str
    error: str