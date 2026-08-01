from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal

# Single-sourced from the sampler's config so the API reports, validates, and
# defaults to exactly what video_util_get_frame_interval() uses.
from app.config.settings import (
    VIDEO_FRAME_INTERVAL_SECONDS,
    VIDEO_FRAME_INTERVAL_MIN,
    VIDEO_FRAME_INTERVAL_MAX,
)


class MemoryScoringWeights(BaseModel):
    """
    Relative importance of each memory scoring signal.

    Weights are normalized to sum to 1.0 on validation, so a UI slider set
    never has to land on an exact total.
    """

    favourite: float = Field(default=0.22, ge=0.0, le=1.0)
    known_people: float = Field(default=0.20, ge=0.0, le=1.0)
    event_strength: float = Field(default=0.18, ge=0.0, le=1.0)
    face_presence: float = Field(default=0.12, ge=0.0, le=1.0)
    semantic_confidence: float = Field(default=0.10, ge=0.0, le=1.0)
    gps_novelty: float = Field(default=0.10, ge=0.0, le=1.0)
    in_album: float = Field(default=0.08, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _normalize(self) -> "MemoryScoringWeights":
        names = list(type(self).model_fields)
        total = sum(getattr(self, name) for name in names)
        # An all-zero set carries no ranking information; fall back to defaults
        # rather than dividing by zero.
        if total <= 0:
            for name in names:
                object.__setattr__(self, name, type(self).model_fields[name].default)
            return self
        for name in names:
            object.__setattr__(self, name, getattr(self, name) / total)
        return self


class MemoriesPreferences(BaseModel):
    """Memory generation and delivery preferences."""

    enabled: bool = True
    notifications_enabled: bool = True
    # The story viewer ships muted; the user opts into background audio.
    story_music_enabled: bool = False
    # Seconds each photo is held before the story advances. A video slide
    # runs for its own length instead.
    slide_duration_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    # Short clips shot during the same span, as punctuation between stills.
    include_videos: bool = True
    min_images: int = Field(default=5, ge=2, le=50)
    max_images: int = Field(default=30, ge=5, le=100)
    weights: MemoryScoringWeights = Field(default_factory=MemoryScoringWeights)

    @model_validator(mode="after")
    def _check_bounds(self) -> "MemoriesPreferences":
        if self.max_images < self.min_images:
            raise ValueError("max_images must be greater than or equal to min_images")
        return self


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
    memories: MemoriesPreferences = Field(default_factory=MemoriesPreferences)


class GetUserPreferencesResponse(BaseModel):
    """Response model for getting user preferences"""

    success: bool
    message: str
    user_preferences: UserPreferencesData


class MemoryScoringWeightsUpdate(BaseModel):
    """
    Partial update for scoring weights.

    Deliberately does not normalize: rescaling a single slider to 1.0 would
    wipe out the others. Stored values stay raw and are normalized on read.
    """

    favourite: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    known_people: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    event_strength: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    face_presence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    semantic_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    gps_novelty: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    in_album: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MemoriesPreferencesUpdate(BaseModel):
    """Partial update for memories preferences; every field is optional."""

    enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    story_music_enabled: Optional[bool] = None
    slide_duration_seconds: Optional[float] = Field(default=None, ge=1.0, le=30.0)
    include_videos: Optional[bool] = None
    min_images: Optional[int] = Field(default=None, ge=2, le=50)
    max_images: Optional[int] = Field(default=None, ge=5, le=100)
    weights: Optional[MemoryScoringWeightsUpdate] = None


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""

    YOLO_model_size: Optional[Literal["nano", "small", "medium"]] = None
    GPU_Acceleration: Optional[bool] = None
    Video_Frame_Interval: Optional[float] = Field(
        default=None, ge=VIDEO_FRAME_INTERVAL_MIN, le=VIDEO_FRAME_INTERVAL_MAX
    )
    memories: Optional[MemoriesPreferencesUpdate] = None


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
