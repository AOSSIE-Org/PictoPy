# Add this to existing folders.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
import asyncio

router = APIRouter()

class BulkTagRequest(BaseModel):
    folder_ids: List[str]

class FolderStatusResponse(BaseModel):
    folder_id: str
    status: str  # 'completed', 'in_progress', 'pending'
    total_images: int
    tagged_images: int
    progress_percentage: float

@router.post("/folders/bulk-tag")
async def bulk_tag_folders(
    request: BulkTagRequest,
    background_tasks: BackgroundTasks
):
    """
    Enable AI tagging for multiple folders at once.
    Processes folders in batches to avoid overwhelming the system.
    """
    if not request.folder_ids:
        raise HTTPException(status_code=400, detail="No folders provided")
    
    if len(request.folder_ids) > 50:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 50 folders can be tagged at once"
        )
    
    # Validate all folders exist
    invalid_folders = []
    for folder_id in request.folder_ids:
        folder = db_get_folder_by_id(folder_id)
        if not folder:
            invalid_folders.append(folder_id)
    
    if invalid_folders:
        raise HTTPException(
            status_code=404,
            detail=f"Folders not found: {', '.join(invalid_folders)}"
        )
    
    # Process in background
    background_tasks.add_task(
        process_bulk_tagging,
        request.folder_ids
    )
    
    return {
        "message": f"Started AI tagging for {len(request.folder_ids)} folders",
        "folder_ids": request.folder_ids,
        "status": "processing"
    }

async def process_bulk_tagging(folder_ids: List[str]):
    """
    Process AI tagging for multiple folders.
    Handles batch processing with rate limiting.
    """
    batch_size = 5
    for i in range(0, len(folder_ids), batch_size):
        batch = folder_ids[i:i + batch_size]
        
        # Process batch concurrently
        tasks = [enable_ai_tagging_for_folder(fid) for fid in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Small delay between batches
        if i + batch_size < len(folder_ids):
            await asyncio.sleep(1)

@router.get("/folders/{folder_id}/status", response_model=FolderStatusResponse)
async def get_folder_tagging_status(folder_id: str):
    """
    Get detailed tagging status for a specific folder.
    """
    folder = db_get_folder_by_id(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    total_images = db_count_images_in_folder(folder_id)
    tagged_images = db_count_tagged_images_in_folder(folder_id)
    
    if total_images == 0:
        status = "empty"
        progress = 0.0
    elif tagged_images == total_images:
        status = "completed"
        progress = 100.0
    elif tagged_images > 0:
        status = "in_progress"
        progress = (tagged_images / total_images) * 100
    else:
        status = "pending"
        progress = 0.0
    
    return FolderStatusResponse(
        folder_id=folder_id,
        status=status,
        total_images=total_images,
        tagged_images=tagged_images,
        progress_percentage=round(progress, 2)
    )

@router.post("/folders/bulk-status")
async def get_bulk_folder_status(request: BulkTagRequest):
    """
    Get status for multiple folders at once.
    More efficient than individual requests.
    """
    statuses = []
    for folder_id in request.folder_ids:
        try:
            status = await get_folder_tagging_status(folder_id)
            statuses.append(status.dict())
        except HTTPException:
            # Skip invalid folders
            continue
    
    return {"statuses": statuses}
