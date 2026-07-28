from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

EventType = Literal["anniversary", "import_event", "semantic_event"]
MemoryStatus = Literal["pending", "complete", "failed", "empty"]
RunStatus = Literal["running", "complete", "failed"]


class MemoryImageItem(BaseModel):
    """A single curated image within a memory."""

    id: str
    path: str
    thumbnailPath: Optional[str] = None
    captured_at: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isFavourite: bool = False
    sort_order: int
    score: Optional[float] = None


class MemoryVideoItem(BaseModel):
    """A short clip curated into a memory, sharing the images' sort_order."""

    id: str
    path: str
    thumbnailPath: Optional[str] = None
    captured_at: Optional[str] = None
    duration: Optional[float] = None
    isFavourite: bool = False
    sort_order: int
    score: Optional[float] = None


class MemoryCard(BaseModel):
    """Memory summary, without the image set. Used by the history filmstrip."""

    memory_id: str
    dedupe_key: str
    event_type: EventType
    status: MemoryStatus
    title: str
    subtitle: Optional[str] = None
    place_label: Optional[str] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    surface_date: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    image_count: int = 0
    video_count: int = 0
    cover_image_id: Optional[str] = None
    cover_thumbnail_path: Optional[str] = None
    score: float = 0.0
    notified_at: Optional[str] = None
    viewed_at: Optional[str] = None
    dismissed: bool = False
    created_at: Optional[str] = None


class MemoryStory(MemoryCard):
    """A memory with its full image set, for the story viewer."""

    images: List[MemoryImageItem] = Field(default_factory=list)
    # Separate from images because they are separate tables; sort_order runs
    # across both, so the viewer merges them into one sequence.
    videos: List[MemoryVideoItem] = Field(default_factory=list)
    # Per-signal breakdown kept for debugging why an image was selected. Not
    # surfaced in the UI.
    signals: Optional[Dict[str, Any]] = None


class GenerateMemoriesRequest(BaseModel):
    """Request model for triggering a curation run."""

    force: bool = False
    reference_date: Optional[str] = None


class GenerateMemoriesData(BaseModel):
    """Outcome of a generate call."""

    run_date: str
    status: RunStatus
    queued: bool


class UpdateMemoryRequest(BaseModel):
    """Request model for updating a memory's user-facing state."""

    viewed: Optional[bool] = None
    dismissed: Optional[bool] = None
    notified: Optional[bool] = None


class MemoryStatusData(BaseModel):
    """Scheduler-facing snapshot. Polled by the Tauri background task."""

    run_date: str
    run_status: Optional[RunStatus] = None
    # Identifies *which* run is being reported. Without it a caller cannot
    # tell its own queued run from one that finished earlier the same day,
    # since run_date is only ever today.
    run_started_at: Optional[str] = None
    indexing_busy: bool = False
    unviewed_count: int = 0
    latest_memory_id: Optional[str] = None
    memories_enabled: bool = True
    notifications_enabled: bool = True


class GetMemoriesData(BaseModel):
    """Paginated memory cards."""

    memories: List[MemoryCard] = Field(default_factory=list)
    total_count: int = 0


class GetMemoryData(BaseModel):
    """A single memory story."""

    memory: MemoryStory


class GetTodayMemoryData(BaseModel):
    """
    The memory to surface now, if any.

    `memory` is null rather than a 404 when nothing qualifies: this endpoint is
    polled, and an empty library is a normal state, not an error.
    """

    memory: Optional[MemoryStory] = None


class DeleteMemoryData(BaseModel):
    """Outcome of a delete call."""

    memory_id: str


class GenerateMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: GenerateMemoriesData


class GetMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: GetMemoriesData


class GetMemoryResponse(BaseModel):
    success: bool
    message: str
    data: GetMemoryData


class GetTodayMemoryResponse(BaseModel):
    success: bool
    message: str
    data: GetTodayMemoryData


class MemoryStatusResponse(BaseModel):
    success: bool
    message: str
    data: MemoryStatusData


class UpdateMemoryResponse(BaseModel):
    success: bool
    message: str
    data: GetMemoryData


class DeleteMemoryResponse(BaseModel):
    success: bool
    message: str
    data: DeleteMemoryData


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool
    error: str
    message: str
