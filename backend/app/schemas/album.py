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

    @field_validator("image_ids")
    def validate_image_ids(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("image_ids cannot be empty")

        cleaned = []
        for img_id in value:
            if not img_id or not img_id.strip():
                raise ValueError("image_ids must not contain empty values")
            cleaned.append(img_id.strip())

        return cleaned


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
