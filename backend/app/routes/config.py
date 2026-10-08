from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import (
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
)

router = APIRouter()


@router.get("/supported-extensions")
async def get_supported_extensions():
    """Return the file extensions the app can index and open, without the dot."""
    all_extensions = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS
    return {"data": {"extensions": sorted(ext.lstrip(".") for ext in all_extensions)}}
