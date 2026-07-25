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
    Get tagging and semantic-embedding progress for all folders.

    Returns:
        List of folders with tagging/embedding percentages, raw image
        counts, and each folder's AI_Tagging flag.
    """
    try:
        tagging_progress = db_get_tagging_progress()

        folder_info_list = [
            FolderTaggingInfo(
                folder_id=folder.folder_id,
                folder_path=folder.folder_path,
                tagging_percentage=folder.tagging_percentage,
                embedding_percentage=folder.embedding_percentage,
                total_images=folder.total_images,
                tagged_images=folder.tagged_images,
                embedded_images=folder.embedded_images,
                ai_tagging=folder.ai_tagging,
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
