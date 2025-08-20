from pydantic import BaseModel
from typing import List, Optional


class WatchedFolder(BaseModel):
    """Schema for a watched folder."""

    id: str
    path: str


class WatcherStatusResponse(BaseModel):
    """Watcher status endpoint response schema."""

    is_running: bool
    folders_count: int
    thread_alive: bool
    thread_id: Optional[int]
    watched_folders: List[WatchedFolder]


class WatcherControlResponse(BaseModel):
    """Schema for watcher control operations (start/stop/restart)."""

    success: bool
    message: str
    watcher_info: WatcherStatusResponse


class WatcherErrorResponse(BaseModel):
    """Schema for watcher error responses."""

    detail: str
