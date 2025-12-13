"""API routes for the Memories feature.

Provides endpoints for generating, retrieving, and managing memories.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
from datetime import datetime

from app.schemas.memories import (
    MemoryResponse,
    MemoriesListResponse,
    GenerateMemoriesRequest,
    GenerateMemoriesResponse,
    DeleteMemoryRequest,
    DeleteMemoryResponse,
    ErrorResponse
)
from app.database import memories as memories_db
from app.config.settings import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/memories",
    tags=["memories"],
    responses={404: {"model": ErrorResponse}}
)


@router.post("/generate", response_model=GenerateMemoriesResponse)
async def generate_memories(request: GenerateMemoriesRequest):
    """
    Generate memories based on time and location.
    
    This endpoint analyzes the image gallery and creates automatic memory collections
    based on temporal patterns (e.g., "On this day last year") and geographic clustering
    (e.g., "Trip to Paris 2023").
    
    Args:
        request: Configuration for memory generation
    
    Returns:
        Summary of generated memories
    """
    try:
        conn = get_db_connection()
        
        time_based_count = 0
        location_based_count = 0
        
        # Parse reference date if provided
        reference_date = None
        if request.reference_date:
            try:
                reference_date = datetime.fromisoformat(request.reference_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid reference_date format")
        
        # Generate time-based memories
        if request.include_time_based:
            logger.info("Generating time-based memories...")
            time_memories = memories_db.generate_time_based_memories(
                conn, reference_date
            )
            
            # Save to database
            for memory in time_memories:
                image_ids = [img["id"] for img in memory["images"]]
                memories_db.save_memory(
                    conn=conn,
                    memory_type=memory["type"],
                    title=memory["title"],
                    description=memory["description"],
                    start_date=memory["start_date"],
                    end_date=memory["end_date"],
                    image_ids=image_ids
                )
                time_based_count += 1
        
        # Generate location-based memories
        if request.include_location_based:
            logger.info("Generating location-based memories...")
            location_memories = memories_db.generate_location_based_memories(
                conn,
                min_images=request.min_images_for_location,
                distance_threshold=request.distance_threshold
            )
            
            # Save to database
            for memory in location_memories:
                image_ids = [img["id"] for img in memory["images"]]
                memories_db.save_memory(
                    conn=conn,
                    memory_type=memory["type"],
                    title=memory["title"],
                    description=memory["description"],
                    start_date=memory["start_date"],
                    end_date=memory["end_date"],
                    image_ids=image_ids,
                    location=memory.get("location"),
                    latitude=memory.get("latitude"),
                    longitude=memory.get("longitude")
                )
                location_based_count += 1
        
        total_memories = time_based_count + location_based_count
        
        return GenerateMemoriesResponse(
            success=True,
            message=f"Successfully generated {total_memories} memories",
            time_based_count=time_based_count,
            location_based_count=location_based_count,
            total_memories=total_memories
        )
    
    except Exception as e:
        logger.error(f"Error generating memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=MemoriesListResponse)
async def list_memories():
    """
    Get all generated memories.
    
    Returns a list of all memories that have been created, including both
    time-based and location-based memories.
    
    Returns:
        List of all memories with their metadata and images
    """
    try:
        conn = get_db_connection()
        memories = memories_db.get_all_memories(conn)
        
        # Convert to response format
        memory_responses = []
        for mem in memories:
            cover_image = {
                "id": mem["cover_image_id"],
                "path": mem["images"][0]["path"] if mem["images"] else ""
            }
            
            memory_responses.append(
                MemoryResponse(
                    id=mem["id"],
                    type=mem["type"],
                    title=mem["title"],
                    description=mem["description"],
                    start_date=mem["start_date"],
                    end_date=mem["end_date"],
                    location=mem["location"],
                    latitude=mem["latitude"],
                    longitude=mem["longitude"],
                    cover_image=cover_image,
                    image_count=mem["image_count"],
                    images=mem["images"],
                    created_at=mem["created_at"],
                    last_viewed=mem["last_viewed"]
                )
            )
        
        return MemoriesListResponse(
            memories=memory_responses,
            total_count=len(memory_responses)
        )
    
    except Exception as e:
        logger.error(f"Error listing memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: int):
    """
    Get details of a specific memory.
    
    Args:
        memory_id: ID of the memory to retrieve
    
    Returns:
        Detailed information about the memory including all images
    """
    try:
        conn = get_db_connection()
        memories = memories_db.get_all_memories(conn)
        
        # Find the requested memory
        memory = next((m for m in memories if m["id"] == memory_id), None)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update last viewed timestamp
        memories_db.update_memory_viewed(conn, memory_id)
        
        cover_image = {
            "id": memory["cover_image_id"],
            "path": memory["images"][0]["path"] if memory["images"] else ""
        }
        
        return MemoryResponse(
            id=memory["id"],
            type=memory["type"],
            title=memory["title"],
            description=memory["description"],
            start_date=memory["start_date"],
            end_date=memory["end_date"],
            location=memory["location"],
            latitude=memory["latitude"],
            longitude=memory["longitude"],
            cover_image=cover_image,
            image_count=memory["image_count"],
            images=memory["images"],
            created_at=memory["created_at"],
            last_viewed=memory["last_viewed"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", response_model=DeleteMemoryResponse)
async def delete_memory(request: DeleteMemoryRequest):
    """
    Delete a specific memory.
    
    This will remove the memory and all its associations but will not delete
    the actual images from the gallery.
    
    Args:
        request: Memory ID to delete
    
    Returns:
        Success status of the deletion
    """
    try:
        conn = get_db_connection()
        success = memories_db.delete_memory(conn, request.memory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return DeleteMemoryResponse(
            success=True,
            message=f"Memory {request.memory_id} deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {request.memory_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_memories():
    """
    Refresh all memories by regenerating them.
    
    This endpoint clears all existing memories and regenerates them based on
    the current image gallery. Useful for updating memories after adding new photos.
    
    Returns:
        Summary of regenerated memories
    """
    try:
        conn = get_db_connection()
        
        # Delete all existing memories
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories")
        conn.commit()
        
        logger.info("Cleared existing memories, regenerating...")
        
        # Regenerate memories
        request = GenerateMemoriesRequest(
            include_time_based=True,
            include_location_based=True
        )
        
        return await generate_memories(request)
    
    except Exception as e:
        logger.error(f"Error refreshing memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
