"""Common schema definitions shared across the application."""

from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response model for API errors."""

    success: bool = False
    error: Optional[str] = None
    message: Optional[str] = None
