from fastapi import APIRouter
from typing import Union
from app.database.folders import db_get_tagging_progress
from app.schemas.folders import (
    FolderTaggingStatusSuccessResponse,
    FolderTaggingStatusErrorResponse,
    FolderTaggingInfo,
)

router = APIRouter()


@router.get(
    "/status",
    response_model=Union[
        FolderTaggingStatusSuccessResponse, FolderTaggingStatusErrorResponse
    ],
)
def get_folders_tagging_status():
    """
    Get tagging progress for all folders.

    Returns:
        List of folders with their tagging progress information including:
        - folder_id: Unique identifier for the folder
        - folder_path: Path to the folder
        - tagging_percentage: Percentage of images that have been tagged (0-100)
    """
    try:
        tagging_progress = db_get_tagging_progress()

        folder_info_list = [
            FolderTaggingInfo(
                folder_id=folder.folder_id,
                folder_path=folder.folder_path,
                tagging_percentage=folder.tagging_percentage,
            )
            for folder in tagging_progress
        ]

        return FolderTaggingStatusSuccessResponse(
            status="success",
            data=folder_info_list,
            total_folders=len(tagging_progress),
        )
    except Exception as e:
        return FolderTaggingStatusErrorResponse(
            status="error",
            message=f"Failed to retrieve tagging progress: {str(e)}",
        )
