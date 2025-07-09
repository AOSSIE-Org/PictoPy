from pydantic import BaseModel
from typing import Optional, List


# Request Models
class AddFolderRequest(BaseModel):
    folder_path: str
    parent_folder_id: Optional[str] = None  # UUID as string
    AI_Tagging: Optional[bool] = False
    taggingCompleted: Optional[bool] = False
    # app: FastAPI


class UpdateAITaggingRequest(BaseModel):
    folder_ids: List[str]  # List of folder UUIDs


# Response Models
class AddFolderResponse(BaseModel):
    success: bool
    message: str
    folder_id: Optional[str] = None  # UUID as string


class UpdateAITaggingResponse(BaseModel):
    success: bool
    message: str
    updated_count: int


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
