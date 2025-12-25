from pydantic import BaseModel
from typing import List, Optional


class MemoryImage(BaseModel):
    id: str
    path: str
    thumbnail: str
    date: str
    location: Optional[str] = None


class Memory(BaseModel):
    id: str
    title: str
    description: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_count: int
    images: List[MemoryImage]


class GetMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: List[Memory]


class GetMemoryImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[MemoryImage]


class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str
