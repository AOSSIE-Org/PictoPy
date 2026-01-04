from pydantic import BaseModel
from typing import List

class BatchDeleteRequest(BaseModel):
    """Request model for batch delete operation"""
    image_ids: List[str]

class BatchTagRequest(BaseModel):
    """Request model for batch tag operation"""
    image_ids: List[str]
    tags: List[str]

class BatchMoveRequest(BaseModel):
    """Request model for batch move to album operation"""
    image_ids: List[str]
    album_id: str

class BatchOperationResponse(BaseModel):
    """Response model for batch operations"""
    success: bool
    processed: int
    failed: int
    errors: List[str] = []
