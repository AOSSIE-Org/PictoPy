from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Union


class InputType(str, Enum):
    path = "path"
    base64 = "base64"


class FaceSearchRequest(BaseModel):
    path: Optional[str] = None
    base64_data: Optional[str] = None


class AddMultipleImagesRequest(BaseModel):
    paths: List[str]


class DeleteImageRequest(BaseModel):
    path: str


class DeleteMultipleImagesRequest(BaseModel):
    paths: List[str]
    isFromDevice: bool


class AddFolderRequest(BaseModel):
    folder_path: List[str]


class GenerateThumbnailsRequest(BaseModel):
    folder_paths: List[str]


class DeleteThumbnailsRequest(BaseModel):
    folder_path: str


# Response Model
class FaceTaggingResponse(BaseModel):
    success: bool
    message: str
    data: dict


class ImagesResponse(BaseModel):
    image_files: List[str]
    folder_path: str


class GetImagesResponse(BaseModel):
    success: bool
    message: str
    data: ImagesResponse


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str


class AddMultipleImagesResponse(BaseModel):
    data: int
    message: str
    success: bool


class DeleteImageResponse(BaseModel):
    data: str
    message: str
    success: bool


class DeleteMultipleImagesResponse(BaseModel):
    data: List[str]
    message: str
    success: bool


class GetAllImageObjectsResponse(BaseModel):
    success: bool
    message: str
    data: dict


class ClassIDsResponse(BaseModel):
    success: bool
    message: str
    data: Union[List[str], str]


class AddFolderResponse(BaseModel):
    data: int
    message: str
    success: bool


class FailedPathResponse(BaseModel):
    folder_path: str
    error: str
    message: str
    file: Optional[str] = None


class GenerateThumbnailsResponse(BaseModel):
    success: bool
    message: str
    failed_paths: Optional[List[FailedPathResponse]] = None


class FailedDeletionThumbnailResponse(BaseModel):
    folder: str
    error: str


class DeleteThumbnailsFailedResponse(BaseModel):
    success: bool = False
    message: str
    error: str
    failed_deletions: List[dict | None]


class DeleteThumbnailsResponse(BaseModel):
    success: bool
    message: str
    failed_deletions: Optional[List[FailedDeletionThumbnailResponse]] = None


class GetThumbnailPathResponse(BaseModel):
    success: bool
    thumbnailPath: str
