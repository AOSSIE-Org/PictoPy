from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List

from app.schemas.memories import (
    GenerateMemoriesRequest,
    GetAllMemoriesResponse,
    GetMemoryDetailResponse,
    GenerateMemoriesResponse,
    DeleteMemoryResponse,
    ErrorResponse,
    MemorySummary,
    MemoryDetail,
    ImageInMemory,
)
from app.database.memories import (
    db_get_all_memories,
    db_get_memory_by_id,
    db_delete_memory,
)
from app.utils.memory_generator import MemoryGenerator
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=GetAllMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_memories():
    """
    Get all memories with their representative images.
    Returns memories sorted by date (most recent first).
    """
    try:
        memories_data = db_get_all_memories()

        memories = [
            MemorySummary(
                id=m["id"],
                title=m["title"],
                memory_type=m["memory_type"],
                start_date=m["start_date"],
                end_date=m["end_date"],
                location=m.get("location"),
                latitude=m.get("latitude"),
                longitude=m.get("longitude"),
                total_photos=m["total_photos"],
                representative_thumbnails=m.get("representative_thumbnails", []),
                created_at=m["created_at"],
            )
            for m in memories_data
        ]

        return GetAllMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} memories",
            data=memories,
        )

    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memories: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/{memory_id}",
    response_model=GetMemoryDetailResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_memory_detail(memory_id: str):
    """
    Get detailed information about a specific memory including all its images.
    """
    try:
        memory_data = db_get_memory_by_id(memory_id)

        if not memory_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not found",
                    message=f"Memory with ID {memory_id} not found",
                ).model_dump(),
            )

        images = [
            ImageInMemory(
                id=img["id"],
                path=img["path"],
                thumbnailPath=img["thumbnailPath"],
                metadata=img["metadata"],
                is_representative=img["is_representative"],
            )
            for img in memory_data["images"]
        ]

        memory = MemoryDetail(
            id=memory_data["id"],
            title=memory_data["title"],
            memory_type=memory_data["memory_type"],
            start_date=memory_data["start_date"],
            end_date=memory_data["end_date"],
            location=memory_data.get("location"),
            latitude=memory_data.get("latitude"),
            longitude=memory_data.get("longitude"),
            cover_image_id=memory_data.get("cover_image_id"),
            total_photos=memory_data["total_photos"],
            created_at=memory_data["created_at"],
            images=images,
        )

        return GetMemoryDetailResponse(
            success=True, message="Memory retrieved successfully", data=memory
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memory: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/generate",
    response_model=GenerateMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def generate_memories(request: GenerateMemoriesRequest):
    """
    Generate memories from existing photos based on date and location.
    This process analyzes all photos and creates automatic memory collections.
    
    - Set force_regenerate=true to clear existing memories and regenerate all
    - Memory generation happens synchronously and may take time for large galleries
    """
    try:
        logger.info(
            f"Starting memory generation (force_regenerate={request.force_regenerate})"
        )

        generator = MemoryGenerator()
        result = generator.generate_all_memories(
            force_regenerate=request.force_regenerate
        )

        return GenerateMemoriesResponse(
            success=True,
            message=result["message"],
            data={
                "memories_created": result["memories_created"],
                "stats": result["stats"],
            },
        )

    except Exception as e:
        logger.error(f"Error generating memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to generate memories: {str(e)}",
            ).model_dump(),
        )


@router.delete(
    "/{memory_id}",
    response_model=DeleteMemoryResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_memory(memory_id: str):
    """
    Delete a specific memory.
    Note: This only deletes the memory entry, not the actual photos.
    """
    try:
        success = db_delete_memory(memory_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not found",
                    message=f"Memory with ID {memory_id} not found or already deleted",
                ).model_dump(),
            )

        return DeleteMemoryResponse(
            success=True, message=f"Memory {memory_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to delete memory: {str(e)}",
            ).model_dump(),
        )