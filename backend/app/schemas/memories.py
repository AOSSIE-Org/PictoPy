from pydantic import BaseModel
from typing import List, Optional


class MemoryImageMetadata(BaseModel):
    name: str
    date_created: Optional[str] = None
    width: int
    height: int
    file_location: str
    file_size: int
    item_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


class MemoryImage(BaseModel):
    id: str
    path: str
    thumbnailPath: str
    metadata: MemoryImageMetadata
    isTagged: bool
    tags: Optional[List[str]] = None


class OnThisDayMemory(BaseModel):
    year: int
    years_ago: int
    date: str
    images: List[MemoryImage]


class RecentMemory(BaseModel):
    date: str
    iso_date: str
    images: List[MemoryImage]


class PersonMemory(BaseModel):
    cluster_id: str
    person_name: str
    image_count: int
    images: List[MemoryImage]


class TagMemory(BaseModel):
    tag_name: str
    image_count: int
    images: List[MemoryImage]


class OnThisDayResponse(BaseModel):
    success: bool
    message: str
    data: List[OnThisDayMemory]


class RecentMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: List[RecentMemory]


class PeopleMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: List[PersonMemory]


class TagMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: List[TagMemory]


class AllMemoriesData(BaseModel):
    on_this_day: List[OnThisDayMemory]
    recent: List[RecentMemory]
    people: List[PersonMemory]
    tags: List[TagMemory]


class AllMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: AllMemoriesData


class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str
