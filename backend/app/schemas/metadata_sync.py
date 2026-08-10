from pydantic import BaseModel


class MetadataSyncStatus(BaseModel):
    """How far behind the files are, and whether writing to them is allowed."""

    enabled: bool
    pending: int


class GetMetadataSyncStatusResponse(BaseModel):
    success: bool
    message: str
    data: MetadataSyncStatus


class MetadataSyncResult(BaseModel):
    """What one pass did. `skipped` counts photos left for a later attempt."""

    considered: int
    written: int
    skipped: int


class RunMetadataSyncResponse(BaseModel):
    success: bool
    message: str
    data: MetadataSyncResult


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool
    error: str
    message: str
