from pydantic import BaseModel, Field
from typing import Optional, Literal

# Single-sourced from the sampler's config so the API reports, validates, and
# defaults to exactly what video_util_get_frame_interval() uses.
from app.config.settings import (
    VIDEO_FRAME_INTERVAL_SECONDS,
    VIDEO_FRAME_INTERVAL_MIN,
    VIDEO_FRAME_INTERVAL_MAX,
)


class UserPreferencesData(BaseModel):
    """User preferences data structure"""

    YOLO_model_size: Literal["nano", "small", "medium"] = "small"
    GPU_Acceleration: bool = True
    # Seconds between sampled video keyframes. Lower means finer tag coverage
    # and proportionally more inference per video.
    Video_Frame_Interval: float = Field(
        default=VIDEO_FRAME_INTERVAL_SECONDS,
        ge=VIDEO_FRAME_INTERVAL_MIN,
        le=VIDEO_FRAME_INTERVAL_MAX,
    )


class GetUserPreferencesResponse(BaseModel):
    """Response model for getting user preferences"""

    success: bool
    message: str
    user_preferences: UserPreferencesData


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""

    YOLO_model_size: Optional[Literal["nano", "small", "medium"]] = None
    GPU_Acceleration: Optional[bool] = None
    Video_Frame_Interval: Optional[float] = Field(
        default=None, ge=VIDEO_FRAME_INTERVAL_MIN, le=VIDEO_FRAME_INTERVAL_MAX
    )


class UpdateUserPreferencesResponse(BaseModel):
    """Response model for updating user preferences"""

    success: bool
    message: str
    user_preferences: UserPreferencesData


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool
    error: str
    message: str
