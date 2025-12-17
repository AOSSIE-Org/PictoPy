from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from pydantic_core.core_schema import ValidationInfo

# --- Core Models ---

class Album(BaseModel):
    album_id: str
    album_name: str
    description: str
    cover_image_id: Optional[str] = None  # <--- NEW
    is_hidden: bool
    created_at: Optional[str] = None      # <--- NEW
    updated_at: Optional[str] = None      # <--- NEW

class MediaItem(BaseModel):               # <--- NEW (For mixed media)
    media_id: str
    media_type: str  # 'image' or 'video'

# ##############################
# Request Handler
# ##############################

class CreateAlbumRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    cover_image_id: Optional[str] = None  # <--- NEW
    is_hidden: bool = False
    password: Optional[str] = None

    @field_validator("password")
    def check_password(cls, value, info: ValidationInfo):
        if info.data.get("is_hidden") and not value:
            raise ValueError("Password is required for hidden albums")
        return value

class UpdateAlbumRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    cover_image_id: Optional[str] = None  # <--- NEW
    is_hidden: bool
    current_password: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    def check_password(cls, value, info: ValidationInfo):
        if info.data.get("is_hidden") and not value:
            raise ValueError("Password is required for hidden albums")
        return value

class AddMediaRequest(BaseModel):         # <--- NEW (Replaces ImageIdsRequest)
    media_items: List[MediaItem]

# ##############################
# Response Handler
# ##############################

class GetAlbumsResponse(BaseModel):
    success: bool
    albums: List[Album]

class CreateAlbumResponse(BaseModel):
    success: bool
    album_id: str

class GetAlbumResponse(BaseModel):
    success: bool
    data: Album

class GetAlbumMediaResponse(BaseModel):   # <--- UPDATED (was GetAlbumImagesResponse)
    success: bool
    media_items: List[MediaItem]

class SuccessResponse(BaseModel):
    success: bool
    msg: str

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str