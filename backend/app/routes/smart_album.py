from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.schemas.smart_albums import (
    CreateSmartAlbumRequest,
    CreateFaceAlbumRequest,
    UpdateAlbumRequest,
    SmartAlbumResponse,
    AlbumListResponse,
    AlbumImagesResponse,
)

from app.utils.smart_album import SmartAlbumService
from app.database.smart_album import (
    db_get_smart_album_by_id,
    db_get_all_smart_albums,
)


from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/create_object_album", status_code=status.HTTP_201_CREATED)
def create_object_album(request: CreateSmartAlbumRequest):
    """Create a smart album based on object detection criteria."""
    logger.info(f"Creating object-based smart album: {request.album_name}")
    try:
        album_id = SmartAlbumService.create_object_based_album(
            album_name=request.album_name,
            object_classes=request.object_classes,
            auto_update=request.auto_update
        )
        album = db_get_smart_album_by_id(album_id)

        if not album:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve the created album."
            )
        
        return {
            "success": True,
            "album": SmartAlbumResponse(**album),
            "message": f"Smart album '{request.album_name}' created successfully."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating object-based smart album: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the smart album."
        )

@router.post("/create_face_album", status_code=status.HTTP_201_CREATED)
def create_face_album(request: CreateFaceAlbumRequest):
    """Create a smart album based on face recognition criteria."""
    logger.info(f"Creating face-based smart album: {request.album_name}")
    try:
        album_id = SmartAlbumService.create_face_based_album(
            album_name=request.album_name,
            face_id=request.face_id,
            auto_update=request.auto_update
        )

        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve the created album."
            )
        
        return {
            "success": True,
            "album": SmartAlbumResponse(**album),
            "message": f"Smart album '{request.album_name}' created successfully."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating face-based smart album: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create face-based smart album: {e}"
        )

@router.post("/predefine_smart_albums", status_code=status.HTTP_201_CREATED)
def predefine_smart_albums():
    """Predefine a set of common smart albums based on popular object classes."""
    logger.info("Predefining common smart albums.")
    try:
        created = SmartAlbumService.create_predefined_album()  
        albums = []
        for album_id in created.values():  
            album = db_get_smart_album_by_id(album_id)
            if album:
                albums.append(SmartAlbumResponse(**album))  

        return {
            "success": True,
            "albums": albums,
            "created_count": len(albums),  
            "message": f"Created {len(albums)} predefined smart albums."
        }
    except Exception as e:
        logger.error(f"Error predefining smart albums: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predefine smart albums: {e}"
        )

@router.get("/albums", response_model=AlbumListResponse)
def list_smart_albums():
    """Get all smart albums with metadata."""
    logger.info("Fetching all smart albums.")
    try:
        albums_response = db_get_all_smart_albums()
        album_responses = [SmartAlbumResponse(**album) for album in albums_response] 
        return AlbumListResponse(  
            success=True,
            albums=album_responses,
            count=len(album_responses)
        )
    except Exception as e:
        logger.error(f"Error fetching smart albums: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve albums: {str(e)}"
        )

@router.get("/{album_id}") 
def get_album_details(album_id: str):
    """Get details of a specific smart album by ID."""
    logger.info(f"Fetching details for smart album ID: {album_id}")
    try:
        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found."
            )
        return {
            "success": True,
            "album": SmartAlbumResponse(**album),
        }
    except HTTPException:
        raise
    except Exception as e:  
        logger.error(f"Error fetching album details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve album details: {str(e)}"
        )

@router.get("/{album_id}/images", response_model=AlbumImagesResponse)
def get_album_images(
    album_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip for pagination")
):
    """Get images belonging to a specific smart album by ID."""
    logger.info(f"Fetching images for smart album ID: {album_id} with limit={limit} and offset={offset}")
    try:
        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Smart album with ID: {album_id} not found."
            )
        images = SmartAlbumService.get_album_images(
            album_id=album_id,
            limit=limit,
            offset=offset
        )

        return AlbumImagesResponse(
            success=True,
            album_id=album_id,
            images=images,
            count=len(images),
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching album images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve album images: {str(e)}"
        )

@router.post("/{album_id}/refresh", status_code=status.HTTP_200_OK)
def refresh_smart_album(album_id: str):
    """Refresh a smart album to update its images based on current criteria."""
    logger.info(f"Refreshing smart album ID: {album_id}")
    try:
        updated_image_count = SmartAlbumService.refresh_album(album_id=album_id) 
        album = db_get_smart_album_by_id(album_id)  
        
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Smart album with ID: {album_id} not found."
            )
        
        return {
            "success": True,
            "album_id": album_id,
            "updated_image_count": updated_image_count,
            "album": SmartAlbumResponse(**album),
            "message": f"Smart album '{album['album_name']}' refreshed successfully with {updated_image_count} images."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refreshing smart album: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh smart album: {str(e)}"
        )

@router.post("/refresh_all")
def refresh_all_smart_albums():
    """Refresh all smart albums in the system."""
    logger.info("Refreshing all smart albums.")
    try:
        results = SmartAlbumService.refresh_all_albums()
        total_images = sum(results.values())

        albums = db_get_all_smart_albums()
        album_responses = [SmartAlbumResponse(**album) for album in albums]
        
        return {
            "success": True,
            "refreshed_albums": results,
            "albums": album_responses,
            "album_count": len(results),
            "total_images": total_images,
            "message": f"Refreshed {len(results)} smart albums with a total of {total_images} images."
        }
    except Exception as e:
        logger.error(f"Error refreshing all smart albums: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh all smart albums: {str(e)}"
        )

@router.patch("/{album_id}")
def update_smart_album(album_id: str, request: UpdateAlbumRequest):
    """Update smart album details."""
    logger.info(f"Updating smart album ID: {album_id}")
    try:
        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Smart album with ID: {album_id} not found."
            )
        
        SmartAlbumService.update_album( 
            album_id=album_id,
            album_name=request.album_name,
            auto_update=request.auto_update
        )
        
        # ✅ Fetch updated album
        updated_album = db_get_smart_album_by_id(album_id)

        return {
            "success": True,
            "album": SmartAlbumResponse(**updated_album),
            "message": f"Smart album '{updated_album['album_name']}' updated successfully."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating smart album: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update smart album: {str(e)}"
        )

@router.delete("/{album_id}", status_code=status.HTTP_200_OK)
def delete_smart_album(album_id: str):
    """Delete a smart album by ID."""
    logger.info(f"Deleting smart album ID: {album_id}")
    try:
        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Smart album with ID: {album_id} not found."
            )
        
        album_name = album["album_name"]
        SmartAlbumService.delete_album(album_id)

        return {
            "success": True,
            "album_id": album_id,
            "message": f"Smart album '{album_name}' deleted successfully."
        }
    except Exception as e:
        logger.error(f"Error deleting smart album: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete smart album: {str(e)}"
        )

@router.get("/classes/available")
def get_available_classes():
    """Get a list of available object classes for smart albums."""
    logger.info("Fetching available object classes for smart albums.")
    try:
        classes = SmartAlbumService.get_available_object_classes()
        return {
            "success": True,
            "available_classes": classes,
            "count": len(classes),
            "message": "Available object classes retrieved successfully."
        }
    except Exception as e:
        logger.error(f"Error fetching available object classes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available object classes: {str(e)}"
        )

@router.get("/stats/overview")
def get_album_statistics():
    """Get overview statistics about smart albums"""
    try:
        stats = SmartAlbumService.get_album_statistics()
        return {
            "success": True,
            "statistics": stats,
            "message": "Statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )