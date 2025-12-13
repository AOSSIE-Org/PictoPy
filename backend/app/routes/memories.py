import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.database.memories import (
    db_get_all_memories,
    db_get_memory_by_id,
)
from app.utils.memories import generate_memories
from app.database.images import db_get_all_images
from app.utils.images import image_util_parse_metadata

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class MemoryImageData(BaseModel):
    id: str
    path: str
    thumbnailPath: str
    metadata: dict


class MemoryData(BaseModel):
    memory_id: str
    title: str
    memory_type: str
    date_range_start: str
    date_range_end: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_count: int
    representative_image: Optional[MemoryImageData] = None
    year: int


class GetMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: List[MemoryData]


class GenerateMemoriesResponse(BaseModel):
    success: bool
    message: str
    data: dict


class MemoryImagesData(BaseModel):
    memory: MemoryData
    images: List[MemoryImageData]


class GetMemoryImagesResponse(BaseModel):
    success: bool
    message: str
    data: MemoryImagesData


class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str


@router.get(
    "/",
    response_model=GetMemoriesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_all_memories():
    """Get all memories."""
    try:
        logger.info("Fetching all memories...")
        memories = db_get_all_memories()
        
        # Get all images for lookup
        all_images = db_get_all_images()
        images_dict = {img['id']: img for img in all_images}
        
        memory_data_list = []
        
        for memory in memories:
            # Parse image_ids
            try:
                image_ids = json.loads(memory['image_ids'])
            except (json.JSONDecodeError, TypeError):
                image_ids = []
            
            # Get representative image
            representative_image = None
            if memory.get('representative_image_id') and memory['representative_image_id'] in images_dict:
                img = images_dict[memory['representative_image_id']]
                metadata = image_util_parse_metadata(img.get('metadata', {}))
                representative_image = MemoryImageData(
                    id=img['id'],
                    path=img['path'],
                    thumbnailPath=img.get('thumbnailPath', ''),
                    metadata=metadata,
                )
            
            memory_data = MemoryData(
                memory_id=memory['memory_id'],
                title=memory['title'],
                memory_type=memory['memory_type'],
                date_range_start=memory['date_range_start'],
                date_range_end=memory['date_range_end'],
                location_name=memory.get('location_name'),
                latitude=memory.get('latitude'),
                longitude=memory.get('longitude'),
                image_count=len(image_ids),
                representative_image=representative_image,
                year=memory['year'],
            )
            
            memory_data_list.append(memory_data)
        
        logger.info(f"Successfully fetched {len(memory_data_list)} memories")
        
        return GetMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memory_data_list)} memories.",
            data=memory_data_list,
        )
    
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=str(e),
            ).model_dump(),
        )


@router.get(
    "/{memory_id}/images",
    response_model=GetMemoryImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def get_memory_images(memory_id: str):
    """Get all images for a specific memory."""
    try:
        logger.info(f"Fetching images for memory {memory_id}...")
        
        memory = db_get_memory_by_id(memory_id)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Memory Not Found",
                    message=f"Memory with ID {memory_id} not found.",
                ).model_dump(),
            )
        
        # Parse image_ids
        try:
            image_ids = json.loads(memory['image_ids'])
        except (json.JSONDecodeError, TypeError):
            image_ids = []
        
        # Get all images
        all_images = db_get_all_images()
        images_dict = {img['id']: img for img in all_images}
        
        # Get images for this memory
        memory_images = []
        for img_id in image_ids:
            if img_id in images_dict:
                img = images_dict[img_id]
                metadata = image_util_parse_metadata(img.get('metadata', {}))
                memory_images.append(
                    MemoryImageData(
                        id=img['id'],
                        path=img['path'],
                        thumbnailPath=img.get('thumbnailPath', ''),
                        metadata=metadata,
                    )
                )
        
        # Get representative image
        representative_image = None
        if memory.get('representative_image_id') and memory['representative_image_id'] in images_dict:
            img = images_dict[memory['representative_image_id']]
            metadata = image_util_parse_metadata(img.get('metadata', {}))
            representative_image = MemoryImageData(
                id=img['id'],
                path=img['path'],
                thumbnailPath=img.get('thumbnailPath', ''),
                metadata=metadata,
            )
        
        memory_data = MemoryData(
            memory_id=memory['memory_id'],
            title=memory['title'],
            memory_type=memory['memory_type'],
            date_range_start=memory['date_range_start'],
            date_range_end=memory['date_range_end'],
            location_name=memory.get('location_name'),
            latitude=memory.get('latitude'),
            longitude=memory.get('longitude'),
            image_count=len(image_ids),
            representative_image=representative_image,
            year=memory['year'],
        )
        
        result_data = MemoryImagesData(
            memory=memory_data,
            images=memory_images,
        )
        
        logger.info(f"Successfully fetched {len(memory_images)} images for memory")
        
        return GetMemoryImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(memory_images)} images.",
            data=result_data,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching memory images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=str(e),
            ).model_dump(),
        )


@router.post(
    "/generate",
    response_model=GenerateMemoriesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def generate_memories_endpoint():
    """Manually trigger memory generation."""
    try:
        logger.info("Manual memory generation triggered...")
        
        count = generate_memories()
        
        return GenerateMemoriesResponse(
            success=True,
            message=f"Successfully generated {count} memories.",
            data={"memories_created": count},
        )
    
    except Exception as e:
        logger.error(f"Error generating memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=str(e),
            ).model_dump(),
        )
