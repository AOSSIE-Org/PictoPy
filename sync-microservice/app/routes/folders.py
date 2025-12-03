from fastapi import APIRouter
from typing import Union
import time
import sqlite3
from app.database.folders import db_get_tagging_progress
from app.schemas.folders import (
    FolderTaggingStatusSuccessResponse,
    FolderTaggingStatusErrorResponse,
    FolderTaggingInfo,
)

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get(
    "/status",
    response_model=Union[
        FolderTaggingStatusSuccessResponse, FolderTaggingStatusErrorResponse
    ],
)
def get_folders_tagging_status():
    """
    Get tagging progress for all folders with better error handling.
    """
    try:
        
        start_time = time.time()
        
        tagging_progress = db_get_tagging_progress()

        folder_info_list = [
            FolderTaggingInfo(
                folder_id=folder.folder_id,
                folder_path=folder.folder_path,
                total_images=folder.total_images,  
                tagged_images=folder.tagged_images,  
                tagging_percentage=folder.tagging_percentage,
            )
            for folder in tagging_progress
        ]

       
        response = FolderTaggingStatusSuccessResponse(
            status="success",
            data=folder_info_list,
            total_folders=len(tagging_progress),
        )
        
       
        print(f"Tagging status API: {len(folder_info_list)} folders in {round((time.time() - start_time)*1000)}ms")
        
        return response
        
    except sqlite3.Error as e:
        
        return FolderTaggingStatusErrorResponse(
            status="error",
            message="Database connection issue - please try again",
            data=[],
            total_folders=0
        )
    except Exception as e:
        
        return FolderTaggingStatusErrorResponse(
            status="error",
            message="Service temporarily unavailable",
            data=[],
            total_folders=0
        )
