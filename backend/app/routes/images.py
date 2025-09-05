"""
Images API Routes Module

This module provides RESTful API endpoints for image management operations.
It handles retrieving image data, including metadata, tags, and folder associations.

Key Features:
- Retrieve all images with their associated tags
- Structured response models for consistent API responses
- Error handling with appropriate HTTP status codes
- Integration with database layer for data persistence
"""

# Standard library imports
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Application imports
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse

# Create API router for image-related endpoints
router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ImageData(BaseModel):
    """
    Data model representing a single image with its metadata and tags.
    
    Attributes:
        id: Unique identifier for the image
        path: File system path to the image
        folder_id: ID of the folder containing the image
        thumbnailPath: Path to the image thumbnail
        metadata: JSON string containing image metadata
        isTagged: Boolean indicating if the image has been processed for tags
        tags: Optional list of tags associated with the image
    """
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: str
    isTagged: bool
    tags: Optional[List[str]] = None


class GetAllImagesResponse(BaseModel):
    """
    Response model for the get all images endpoint.
    
    Attributes:
        success: Boolean indicating if the operation was successful
        message: Human-readable message describing the result
        data: List of ImageData objects containing the image information
    """
    success: bool
    message: str
    data: List[ImageData]


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get(
    "/",
    response_model=GetAllImagesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_images():
    """
    Retrieve all images from the database with their associated tags.
    
    This endpoint fetches all images stored in the database along with their
    metadata, tags, and folder associations. The response includes both
    tagged and untagged images.
    
    Returns:
        GetAllImagesResponse: Response containing list of all images with metadata
        
    Raises:
        HTTPException: 500 Internal Server Error if database operation fails
    """
    try:
        # Get all images with tags from database using optimized single query
        images = db_get_all_images()

        # Convert database results to response format
        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image["metadata"],
                isTagged=image["isTagged"],
                tags=image["tags"],
            )
            for image in images
        ]

        # Return successful response with image data
        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} images",
            data=image_data,
        )

    except Exception as e:
        # Handle any database or processing errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images: {str(e)}",
            ).model_dump(),
        )
