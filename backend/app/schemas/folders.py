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


# Response Data Models (for the 'data' field)
class FolderDetails(BaseModel):
    folder_id: str
    folder_path: str
    parent_folder_id: Optional[str] = None
    last_modified_time: int
    AI_Tagging: bool
    taggingCompleted: Optional[bool] = None


class GetAllFoldersData(BaseModel):
    folders: List[FolderDetails]
    total_count: int


class AddFolderData(BaseModel):
    folder_id: str  # UUID as string
    folder_path: str


class UpdateAITaggingData(BaseModel):
    updated_count: int
    folder_ids: List[str]


class DeleteFoldersData(BaseModel):
    deleted_count: int
    folder_ids: List[str]


class SyncFolderData(BaseModel):
    deleted_count: int
    deleted_folders: List[str]  # List of folder paths that were deleted
    added_count: int
    added_folders: List[str]  # List of folder paths that were added
    folder_id: str
    folder_path: str


# Response Models
class GetAllFoldersResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[GetAllFoldersData] = None


class AddFolderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[AddFolderData] = None


class UpdateAITaggingResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[UpdateAITaggingData] = None


class DeleteFoldersResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[DeleteFoldersData] = None


class SyncFolderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[SyncFolderData] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: Optional[str] = None
    error: Optional[str] = None
