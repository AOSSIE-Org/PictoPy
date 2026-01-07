from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Common error response model used across all endpoints"""
    success: bool = False
    message: str
    error: str


class SuccessResponse(BaseModel):
    """Common success response model"""
    success: bool
    message: str