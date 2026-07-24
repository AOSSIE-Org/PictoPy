from pydantic import BaseModel, Field
from typing import Optional, Literal


class UserPreferencesData(BaseModel):
    """User preferences data structure"""

    YOLO_model_size: Literal["nano", "small", "medium"] = "small"
    GPU_Acceleration: bool = True
    # Seconds between sampled video keyframes. Lower means finer tag coverage
    # and proportionally more inference per video.
    Video_Frame_Interval: float = Field(default=5.0, ge=1.0, le=60.0)


class GetUserPreferencesResponse(BaseModel):
    """Response model for getting user preferences"""

    success: bool
    message: str
    user_preferences: UserPreferencesData


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""

    YOLO_model_size: Optional[Literal["nano", "small", "medium"]] = None
    GPU_Acceleration: Optional[bool] = None
    Video_Frame_Interval: Optional[float] = Field(default=None, ge=1.0, le=60.0)


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
