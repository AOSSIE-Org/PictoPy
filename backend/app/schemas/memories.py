from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MemoryBase(BaseModel):
    title: str = Field(..., description="Title of the memory")
    description: Optional[str] = Field(None, description="Description of the memory")
    memory_type: str = Field(..., description="Type of memory (on_this_day, location_trip, etc.)")
    date_range_start: str = Field(..., description="Start date of the memory period")
    date_range_end: str = Field(..., description="End date of the memory period")
    location: Optional[str] = Field(None, description="Location name")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class MemoryCreate(MemoryBase):
    image_ids: List[str] = Field([], description="List of image IDs in this memory")


class MemoryResponse(MemoryBase):
    id: str = Field(..., description="Unique memory ID")
    image_count: int = Field(0, description="Number of images in this memory")
    cover_image_id: Optional[str] = Field(None, description="ID of the cover image")
    created_at: str = Field(..., description="When the memory was created")
    last_shown_at: Optional[str] = Field(None, description="When the memory was last shown")
    image_ids: List[str] = Field([], description="List of image IDs in this memory")

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int


class GenerateMemoriesResponse(BaseModel):
    success: bool
    generated_count: int
    message: str
