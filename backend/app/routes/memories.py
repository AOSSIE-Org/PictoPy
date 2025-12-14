from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import uuid

from app.database.memories import (
    db_create_memory,
    db_get_all_memories,
    db_get_memory_by_id,
    db_update_memory_last_shown,
    db_delete_memory,
)
from app.utils.memory_generator import generate_all_memories
from app.schemas.memories import (
    MemoryResponse,
    MemoryListResponse,
    GenerateMemoriesResponse,
)
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=MemoryListResponse)
async def get_memories(limit: Optional[int] = None):
    """
    Get all memories.
    
    Args:
        limit: Optional limit on number of memories to return
        
    Returns:
        List of memories
    """
    try:
        memories = db_get_all_memories(limit=limit)
        return {
            "memories": memories,
            "total": len(memories)
        }
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: The memory ID
        
    Returns:
        Memory details
    """
    try:
        memory = db_get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update last shown timestamp
        db_update_memory_last_shown(memory_id)
        
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateMemoriesResponse)
async def generate_memories(background_tasks: BackgroundTasks):
    """
    Generate memories from images based on time and location.
    
    Returns:
        Generation result with count of created memories
    """
    try:
        # Generate memories
        memories = generate_all_memories()
        
        # Save to database
        saved_count = 0
        for memory_data in memories:
            if db_create_memory(memory_data):
                saved_count += 1
        
        return {
            "success": True,
            "generated_count": saved_count,
            "message": f"Successfully generated {saved_count} memories"
        }
    except Exception as e:
        logger.error(f"Error generating memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a memory.
    
    Args:
        memory_id: The memory ID
        
    Returns:
        Success message
    """
    try:
        success = db_delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{memory_id}/view")
async def mark_memory_viewed(memory_id: str):
    """
    Mark a memory as viewed (updates last_shown_at).
    
    Args:
        memory_id: The memory ID
        
    Returns:
        Success message
    """
    try:
        success = db_update_memory_last_shown(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"message": "Memory view recorded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking memory as viewed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
