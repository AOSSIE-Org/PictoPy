from pydantic import BaseModel, Field
from typing import List, Literal


class FolderTaggingInfo(BaseModel):
    """Individual folder tagging information schema."""

    folder_id: str = Field(..., description="Unique identifier for the folder")
    folder_path: str = Field(..., description="Path to the folder")
    tagging_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of images that have been tagged (0-100)",
    )


class FolderTaggingStatusSuccessResponse(BaseModel):
    """Success response schema for folder tagging status."""

    status: Literal["success"]
    data: List[FolderTaggingInfo]
    total_folders: int = Field(..., ge=0, description="Total number of folders")


class FolderTaggingStatusErrorResponse(BaseModel):
    """Error response schema for folder tagging status."""

    status: Literal["error"]
    message: str = Field(..., description="Error message describing what went wrong")
    data: List[FolderTaggingInfo] = Field(
        default_factory=list, description="Empty list on error"
    )
    total_folders: int = Field(
        default=0, description="Total number of folders (0 on error)"
    )
