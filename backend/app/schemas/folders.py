from pydantic import BaseModel
from typing import Optional, List


# Request Models
class AddFolderRequest(BaseModel):
    folder_path: str
    parent_folder_id: Optional[str] = None  # UUID as string
    taggingCompleted: Optional[bool] = False


class UpdateAITaggingRequest(BaseModel):
    folder_ids: List[str]  # List of folder UUIDs


class DeleteFoldersRequest(BaseModel):
    folder_ids: List[str]  # List of folder UUIDs to delete


class SyncFolderRequest(BaseModel):
    folder_path: str  # Path of the folder to sync
    folder_id: str  # UUID of the folder to sync


# Response Models
class AddFolderResponse(BaseModel):
    success: bool
    message: str
    folder_id: Optional[str] = None  # UUID as string


class UpdateAITaggingResponse(BaseModel):
    success: bool
    message: str
    updated_count: int


class DeleteFoldersResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int


class SyncFolderResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int
    deleted_folders: List[str]  # List of folder paths that were deleted
    added_count: int
    added_folders: List[str]  # List of folder paths that were added


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
