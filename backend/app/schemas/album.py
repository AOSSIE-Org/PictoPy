from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from pydantic_core.core_schema import ValidationInfo


class Album(BaseModel):
    album_id: str
    album_name: str
    description: str
    is_hidden: bool


# ##############################
# Request Handler
# ##############################


class CreateAlbumRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
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
    is_hidden: bool
    current_password: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    def check_password(cls, value, info: ValidationInfo):
        if info.data.get("is_hidden") and not value:
            raise ValueError("Password is required for hidden albums")
        return value

class GetAlbumImagesRequest(BaseModel):
    password: Optional[str] = None


class ImageIdsRequest(BaseModel):
    image_ids: List[str]


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
