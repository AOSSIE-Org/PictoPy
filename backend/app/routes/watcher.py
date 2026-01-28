from fastapi import APIRouter, HTTPException
from app.utils.watcher import (
    watcher_util_start_folder_watcher,
    watcher_util_stop_folder_watcher,
    watcher_util_restart_folder_watcher,
    watcher_util_is_watcher_running,
    watcher_util_get_watcher_info,
)
from app.schemas.watcher import (
    WatcherStatusResponse,
    WatcherControlResponse,
)

router = APIRouter()


@router.get("/status", response_model=WatcherStatusResponse)
async def get_watcher_status():
    """Get folder watcher status."""
    return WatcherStatusResponse(**watcher_util_get_watcher_info())


@router.post("/restart", response_model=WatcherControlResponse)
async def restart_watcher():
    """Restart the folder watcher with fresh data from database."""
    try:
        success = watcher_util_restart_folder_watcher()
        if success:
            return WatcherControlResponse(
                success=True,
                message="Folder watcher restarted successfully",
                watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
            )
        else:
            return WatcherControlResponse(
                success=False,
                message="Failed to restart folder watcher",
                watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error restarting watcher: {str(e)}"
        )


@router.post("/stop", response_model=WatcherControlResponse)
async def stop_watcher():
    """Stop the folder watcher."""
    try:
        watcher_util_stop_folder_watcher()
        return WatcherControlResponse(
            success=True,
            message="Folder watcher stopped",
            watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping watcher: {str(e)}")


@router.post("/start", response_model=WatcherControlResponse)
async def start_watcher():
    """Start the folder watcher."""
    try:
        if watcher_util_is_watcher_running():
            return WatcherControlResponse(
                success=False,
                message="Watcher is already running",
                watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
            )

        success = watcher_util_start_folder_watcher()
        if success:
            return WatcherControlResponse(
                success=True,
                message="Folder watcher started successfully",
                watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
            )
        else:
            return WatcherControlResponse(
                success=False,
                message="Failed to start folder watcher",
                watcher_info=WatcherStatusResponse(**watcher_util_get_watcher_info()),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting watcher: {str(e)}")
