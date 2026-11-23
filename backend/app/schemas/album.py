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
    # Null for albums that predate these columns; they read as oldest.
    created_at: Optional[str] = None
    # Touched by metadata edits and by adding or removing photos.
    updated_at: Optional[str] = None


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


class CreateAlbumFromMemoryRequest(BaseModel):
    memory_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)

    @field_validator("memory_id", "name")
    def check_not_blank(cls, value: str) -> str:
        # min_length counts the spaces, so "   " would otherwise get through
        # and create an album with a blank name.
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


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


class CreateAlbumFromMemoryData(BaseModel):
    album_id: str
    image_count: int


class CreateAlbumFromMemoryResponse(BaseModel):
    # The {success, message, data} envelope the project standardised on, unlike
    # the flat responses above that predate it.
    success: bool
    message: str
    data: CreateAlbumFromMemoryData


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


class ErrorResponseEnvelope(BaseModel):
    """
    How an ErrorResponse actually reaches the client.

    HTTPException nests whatever it is given under `detail`, so documenting
    ErrorResponse alone would describe a shape no client ever receives.
    """

    detail: ErrorResponse
