from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from pydantic_core.core_schema import ValidationInfo


class Album(BaseModel):
    album_id: str
    album_name: str
    description: str
    is_locked: bool
    cover_image_path: Optional[str] = None
    image_count: int = 0


# ##############################
# Request Handler
# ##############################


class CreateAlbumRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    is_locked: bool = False
    password: Optional[str] = None

    @field_validator("password")
    def check_password(cls, value, info: ValidationInfo):
        if info.data.get("is_locked") and not value:
            raise ValueError("Password is required for locked albums")
        return value


class UpdateAlbumRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    is_locked: bool
    current_password: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    def check_password(cls, value, info: ValidationInfo):
        is_locked = info.data.get("is_locked")
        has_current_password = bool(info.data.get("current_password"))

        if is_locked and not has_current_password and not value:
            raise ValueError(
                "Password is required when locking an album without an existing password"
            )
        return value


class GetAlbumImagesRequest(BaseModel):
    password: Optional[str] = None


class ImageIdsRequest(BaseModel):
    image_ids: List[str]


class SetCoverImageRequest(BaseModel):
    image_id: str = Field(..., min_length=1)


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


class GetAlbumImagesResponse(BaseModel):
    success: bool
    image_ids: List[str]


class SuccessResponse(BaseModel):
    success: bool
    msg: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
