from fastapi import APIRouter, HTTPException, status
from typing import List
from app.database.videos import db_get_all_videos
from app.schemas.videos import GetAllVideosResponse, ErrorResponse, VideoData
from app.utils.images import image_util_parse_metadata
from app.utils.videos import video_util_process_folder_videos
from app.database.folders import db_get_all_folder_details

router = APIRouter()


@router.get(
    "/",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_videos():
    try:
        videos = db_get_all_videos()
        data: List[VideoData] = [
            VideoData(
                id=v["id"],
                path=v["path"],
                folder_id=v.get("folder_id"),
                thumbnailPath=v["thumbnailPath"],
                metadata=image_util_parse_metadata(v.get("metadata")),
            )
            for v in videos
        ]
        return GetAllVideosResponse(
            success=True, message=f"Retrieved {len(data)} videos", data=data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal server error", message=str(e)
            ).model_dump(),
        )


@router.post(
    "/scan",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
async def scan_videos_from_folders():
    try:
        rows = db_get_all_folder_details()
        folder_data = [(r[1], r[0], False) for r in rows]
        video_util_process_folder_videos(folder_data)
        videos = db_get_all_videos()
        data: List[VideoData] = [
            VideoData(
                id=v["id"],
                path=v["path"],
                folder_id=v.get("folder_id"),
                thumbnailPath=v["thumbnailPath"],
                metadata=image_util_parse_metadata(v.get("metadata")),
            )
            for v in videos
        ]
        return GetAllVideosResponse(
            success=True, message=f"Scanned {len(folder_data)} folder(s)", data=data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal server error", message=str(e)
            ).model_dump(),
        )


@router.post(
    "/cleanup",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
async def cleanup_deleted_videos():
    """Clean up database entries for videos that no longer exist on disk."""
    try:
        videos = db_get_all_videos()
        data: List[VideoData] = [
            VideoData(
                id=v["id"],
                path=v["path"],
                folder_id=v.get("folder_id"),
                thumbnailPath=v["thumbnailPath"],
                metadata=image_util_parse_metadata(v.get("metadata")),
            )
            for v in videos
        ]
        return GetAllVideosResponse(
            success=True,
            message=f"Cleanup complete. {len(data)} video(s) remain.",
            data=data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal server error", message=str(e)
            ).model_dump(),
        )
