from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CreateSmartAlbumRequest(BaseModel):
    album_name: str = Field(..., min_length=1, max_length=100, description="Name of the smart album")
    object_classes: List[str] = Field(..., description="List of object class names for the smart album")
    auto_update: bool = Field(default=True, description="Whether the album should auto-update")

class CreateFaceAlbumRequest(BaseModel):
    album_name: str = Field(..., min_length=1, max_length=100, description="Name of the person")
    face_id: str = Field(..., description="UUID of the face from face_embeddings table")
    auto_update: bool = Field(default=True, description="Auto-add new matching images")

class UpdateAlbumRequest(BaseModel):
    album_name: Optional[str] = Field(None, min_length=1, max_length=100)
    auto_update: Optional[bool] = None

    
class SmartAlbumResponse(BaseModel):
    album_id: str
    album_name: str
    album_type: str
    criteria: Dict[str, Any]
    thumbnail_image_id: Optional[str] = None
    created_at: int
    updated_at: int
    auto_update: bool
    image_count: int


class AlbumListResponse(BaseModel):
    success: bool
    albums: List[SmartAlbumResponse]
    count: int


class AlbumImagesResponse(BaseModel):
    success: bool
    album_id: str
    images: List[Dict[str, Any]]
    count: int
    limit: Optional[int]
    offset: int