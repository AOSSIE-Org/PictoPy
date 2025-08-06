from pydantic import BaseModel
from typing import Optional, Literal


class UserPreferencesData(BaseModel):
    """User preferences data structure"""

    YOLO_model_size: Literal["nano", "small", "medium"] = "small"
    GPU_Acceleration: bool = True


class GetUserPreferencesResponse(BaseModel):
    """Response model for getting user preferences"""

    success: bool
    message: str
    user_preferences: UserPreferencesData


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""

    YOLO_model_size: Optional[Literal["nano", "small", "medium"]] = None
    GPU_Acceleration: Optional[bool] = None


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
