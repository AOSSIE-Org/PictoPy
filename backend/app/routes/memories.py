from fastapi import APIRouter, HTTPException, status
from typing import List
from app.database.memories import (
    db_generate_memories,
    db_get_memory_images,
    db_get_memories_for_current_date
)
from app.schemas.memories import (
    Memory,
    MemoryImage,
    GetMemoriesResponse,
    GetMemoryImagesResponse,
    ErrorResponse
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=GetMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_memories():
    """
    Get all generated memories.
    
    Returns memories grouped by time and location, showing representative images.
    """
    try:
        memories_data = db_generate_memories()
        
        # Convert to response format
        memories = []
        for memory in memories_data:
            memory_images = [
                MemoryImage(
                    id=img["id"],
                    path=img["path"],
                    thumbnail=img["thumbnail"],
                    date=img["date"].isoformat(),
                    location=img.get("location")
                )
                for img in memory.get("images", [])
            ]
            
            memories.append(
                Memory(
                    id=memory["id"],
                    title=memory["title"],
                    description=memory["description"],
                    start_date=memory["start_date"],
                    end_date=memory["end_date"],
                    location=memory.get("location"),
                    latitude=memory.get("latitude"),
                    longitude=memory.get("longitude"),
                    image_count=memory["image_count"],
                    images=memory_images
                )
            )
        
        return GetMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} memories",
            data=memories
        )
        
    except Exception as e:
        logger.error(f"Error in get_all_memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memories: {str(e)}"
            ).model_dump()
        )


@router.get(
    "/today",
    response_model=GetMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_memories_for_today():
    """
    Get memories relevant to today's date.
    
    Returns "On this day" style memories from previous years.
    """
    try:
        memories_data = db_get_memories_for_current_date()
        
        # Convert to response format
        memories = []
        for memory in memories_data:
            memory_images = [
                MemoryImage(
                    id=img["id"],
                    path=img["path"],
                    thumbnail=img["thumbnail"],
                    date=img["date"].isoformat(),
                    location=img.get("location")
                )
                for img in memory.get("images", [])
            ]
            
            memories.append(
                Memory(
                    id=memory["id"],
                    title=memory["title"],
                    description=memory["description"],
                    start_date=memory["start_date"],
                    end_date=memory["end_date"],
                    location=memory.get("location"),
                    latitude=memory.get("latitude"),
                    longitude=memory.get("longitude"),
                    image_count=memory["image_count"],
                    images=memory_images
                )
            )
        
        return GetMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} memories for today",
            data=memories
        )
        
    except Exception as e:
        logger.error(f"Error in get_memories_for_today: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memories: {str(e)}"
            ).model_dump()
        )


@router.get(
    "/{memory_id}/images",
    response_model=GetMemoryImagesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_memory_detail(memory_id: str):
    """
    Get all images for a specific memory.
    
    Args:
        memory_id: The unique identifier of the memory
        
    Returns:
        All images associated with the memory
    """
    try:
        images_data = db_get_memory_images(memory_id)
        
        # Convert to response format with defensive metadata handling
        images = []
        for img in images_data:
            # Safely extract metadata
            metadata = img.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            
            images.append(
                MemoryImage(
                    id=img.get("id", ""),
                    path=img.get("path", ""),
                    thumbnail=img.get("thumbnail", ""),
                    date=metadata.get("date_created", ""),
                    location=metadata.get("location")
                )
            )
        
        return GetMemoryImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(images)} images",
            data=images
        )
        
    except Exception as e:
        logger.error(f"Error in get_memory_detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memory images: {str(e)}"
            ).model_dump()
        )
