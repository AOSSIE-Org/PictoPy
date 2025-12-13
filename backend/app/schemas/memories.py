"""Pydantic schemas for Memories API endpoints."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ImageBasic(BaseModel):
    """Basic image information for memory display."""
    id: int
    path: str
    date_taken: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CoverImage(BaseModel):
    """Cover image for a memory."""
    id: int
    path: str


class MemoryResponse(BaseModel):
    """Response model for a single memory."""
    id: Optional[int] = None
    type: str = Field(..., description="Type of memory: 'time_based' or 'location_based'")
    title: str
    description: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cover_image: CoverImage
    image_count: int
    images: List[ImageBasic] = []
    created_at: Optional[str] = None
    last_viewed: Optional[str] = None
    years_ago: Optional[int] = None  # For time-based memories


class MemoriesListResponse(BaseModel):
    """Response model for list of memories."""
    memories: List[MemoryResponse]
    total_count: int


class GenerateMemoriesRequest(BaseModel):
    """Request to generate new memories."""
    include_time_based: bool = True
    include_location_based: bool = True
    reference_date: Optional[str] = None
    min_images_for_location: int = Field(default=5, ge=3, le=20)
    distance_threshold: float = Field(default=0.05, ge=0.01, le=1.0)


class GenerateMemoriesResponse(BaseModel):
    """Response after generating memories."""
    success: bool
    message: str
    time_based_count: int = 0
    location_based_count: int = 0
    total_memories: int = 0


class MemoryDetailRequest(BaseModel):
    """Request to get details of a specific memory."""
    memory_id: int


class DeleteMemoryRequest(BaseModel):
    """Request to delete a memory."""
    memory_id: int


class DeleteMemoryResponse(BaseModel):
    """Response after deleting a memory."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
