from fastapi import APIRouter, HTTPException, Query, Body, Path
import uuid
from app.schemas.album import (
    GetAlbumsResponse,
    CreateAlbumRequest,
    CreateAlbumResponse,
    GetAlbumResponse,
    GetAlbumImagesResponse,
    UpdateAlbumRequest,
    SuccessResponse,
    UnlockRequest,
    ImageIdsRequest,
    Album
)
from app.database.albums import (
    db_get_all_albums,
    db_get_album,
    db_insert_album,
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_add_images_to_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    verify_album_password
)

router = APIRouter()

# GET /albums/ - Get all albums
@router.get("/", response_model=GetAlbumsResponse)
def get_albums(show_hidden: bool = Query(False)):
    albums = db_get_all_albums(show_hidden)
    album_list = []
    for album in albums:
        album_list.append(Album(
            album_id=album[0],
            album_name=album[1],
            description=album[2] or "",
            is_hidden=bool(album[3])
        ))
    return GetAlbumsResponse(success=True, albums=album_list)

# POST /albums/ - Create a new album
@router.post("/", response_model=CreateAlbumResponse)
def create_album(body: CreateAlbumRequest):
    album_id = str(uuid.uuid4())
    try:
        db_insert_album(album_id, body.name, body.description, body.is_hidden, body.password)
        return CreateAlbumResponse(success=True, album_id=album_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create album: {str(e)}")

# GET /albums/{album_id} - Get specific album details
@router.get("/{album_id}", response_model=GetAlbumResponse)
def get_album(album_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    album_obj = Album(
        album_id=album[0],
        album_name=album[1],
        description=album[2] or "",
        is_hidden=bool(album[3])
    )
    return GetAlbumResponse(success=True, data=album_obj)

@router.put("/{album_id}", response_model=SuccessResponse)
def update_album(album_id: str = Path(...), body: UpdateAlbumRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    album_dict = {
        "album_id": album[0],
        "album_name": album[1],
        "description": album[2],
        "is_hidden": bool(album[3]),
        "password_hash": album[4]
    }

    if album_dict["password_hash"]:
        if not body.current_password:
            raise HTTPException(status_code=401, detail="Current password is required to update this album")

        if not verify_album_password(album_id, body.current_password):
            raise HTTPException(status_code=401, detail="Incorrect current password")

    try:
        db_update_album(album_id, body.name, body.description, body.is_hidden, body.password)
        return SuccessResponse(success=True, msg="Album updated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update album: {str(e)}")

# DELETE /albums/{album_id} - Delete an album
@router.delete("/{album_id}", response_model=SuccessResponse)
def delete_album(album_id: str = Path(...)):
    # Check if album exists
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    try:
        db_delete_album(album_id)
        return SuccessResponse(success=True, msg="Album deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete album: {str(e)}")

# GET /albums/{album_id}/images - Get all images in an album
@router.get("/{album_id}/images", response_model=GetAlbumImagesResponse)
def get_album_images(album_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    try:
        image_ids = db_get_album_images(album_id)
        return GetAlbumImagesResponse(success=True, image_ids=image_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get album images: {str(e)}")

# POST /albums/{album_id}/images - Add images to an album
@router.post("/{album_id}/images", response_model=SuccessResponse)
def add_images_to_album(album_id: str = Path(...), body: ImageIdsRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if not body.image_ids:
        raise HTTPException(status_code=400, detail="No image IDs provided")
    
    try:
        db_add_images_to_album(album_id, body.image_ids)
        return SuccessResponse(success=True, msg=f"Added {len(body.image_ids)} images to album")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add images to album: {str(e)}")

# DELETE /albums/{album_id}/images/{image_id} - Remove image from album
@router.delete("/{album_id}/images/{image_id}", response_model=SuccessResponse)
def remove_image_from_album(album_id: str = Path(...), image_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    try:
        db_remove_image_from_album(album_id, image_id)
        return SuccessResponse(success=True, msg="Image removed from album successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove image from album: {str(e)}")

# DELETE /albums/{album_id}/images - Remove multiple images from album
@router.delete("/{album_id}/images", response_model=SuccessResponse)
def remove_images_from_album(album_id: str = Path(...), body: ImageIdsRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if not body.image_ids:
        raise HTTPException(status_code=400, detail="No image IDs provided")
    
    try:
        db_remove_images_from_album(album_id, body.image_ids)
        return SuccessResponse(success=True, msg=f"Removed {len(body.image_ids)} images from album")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove images from album: {str(e)}")

# POST /albums/{album_id}/unlock - Unlock a password-protected album (bonus endpoint)
@router.post("/{album_id}/unlock", response_model=SuccessResponse)
def unlock_album(album_id: str = Path(...), body: UnlockRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if not album[4]:
        raise HTTPException(status_code=400, detail="Album is not password protected")

    if not verify_album_password(album_id, body.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return SuccessResponse(success=True, msg="Album unlocked successfully")
