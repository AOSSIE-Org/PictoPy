from fastapi import APIRouter, HTTPException, status, Query, Body, Path
import uuid
from typing import List

# Updated Schema Imports
from app.schemas.album import (
    GetAlbumsResponse,
    CreateAlbumRequest,
    CreateAlbumResponse,
    GetAlbumResponse,
    UpdateAlbumRequest,
    SuccessResponse,
    ErrorResponse,
    Album,
    AddMediaRequest,
    GetAlbumMediaResponse
)

# Updated Database Imports
from app.database.albums import (
    db_get_all_albums,
    db_get_album_by_name,
    db_get_album,
    db_insert_album,
    db_update_album,
    db_delete_album,
    db_get_album_media,
    db_add_media_to_album,
    db_remove_media_from_album,
    verify_album_password,
)

router = APIRouter()

# GET /albums/ - Get all albums
@router.get("/", response_model=GetAlbumsResponse)
def get_albums(show_hidden: bool = Query(False)):
    albums_data = db_get_all_albums(show_hidden)
    album_list = []
    
    for album in albums_data:
        album_list.append(
            Album(
                album_id=album["album_id"],
                album_name=album["album_name"],
                description=album["description"] or "",
                cover_image_id=album["cover_image_id"], # Fixed: correctly mapping new column
                is_hidden=bool(album["is_hidden"]),
                created_at=str(album["created_at"]),
                updated_at=str(album["updated_at"])
            )
        )
    return GetAlbumsResponse(success=True, albums=album_list)


# POST /albums/ - Create a new album
@router.post("/", response_model=CreateAlbumResponse)
def create_album(body: CreateAlbumRequest):
    existing_album = db_get_album_by_name(body.name)
    if existing_album:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                success=False,
                error="Album Already Exists",
                message=f"Album '{body.name}' is already in the database.",
            ).model_dump(),
        )

    album_id = str(uuid.uuid4())
    try:
        # FIXED: Passing all 6 arguments correctly
        db_insert_album(
            album_id=album_id, 
            album_name=body.name, 
            description=body.description, 
            cover_image_id=body.cover_image_id, 
            is_hidden=body.is_hidden, 
            password=body.password
        )
        return CreateAlbumResponse(success=True, album_id=album_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Failed to create album: {str(e)}",
            ).model_dump(),
        )


# GET /albums/{album_id} - Get specific album details
@router.get("/{album_id}", response_model=GetAlbumResponse)
def get_album(album_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Album Not Found", message="Album not found"
            ).model_dump(),
        )

    try:
        album_obj = Album(
            album_id=album["album_id"],
            album_name=album["album_name"],
            description=album["description"] or "",
            cover_image_id=album["cover_image_id"],
            is_hidden=bool(album["is_hidden"]),
            created_at=str(album["created_at"]),
            updated_at=str(album["updated_at"])
        )
        return GetAlbumResponse(success=True, data=album_obj)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Failed to fetch album: {str(e)}",
            ).model_dump(),
        )


# PUT /albums/{album_id} - Update Album
@router.put("/{album_id}", response_model=SuccessResponse)
def update_album(album_id: str = Path(...), body: UpdateAlbumRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the given ID.",
            ).model_dump(),
        )

    # Use existing values if not provided in body
    current_name = body.name if body.name is not None else album["album_name"]
    current_desc = body.description if body.description is not None else album["description"]
    current_cover = body.cover_image_id if body.cover_image_id is not None else album["cover_image_id"]
    current_hidden = body.is_hidden if body.is_hidden is not None else bool(album["is_hidden"])

    if album["password_hash"]:
        if not body.current_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Missing Password",
                    message="Current password is required to update this album.",
                ).model_dump(),
            )

        if not verify_album_password(album_id, body.current_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Incorrect Password",
                    message="The current password is incorrect.",
                ).model_dump(),
            )

    try:
        # FIXED: Passing all arguments correctly
        db_update_album(
            album_id=album_id, 
            album_name=current_name, 
            description=current_desc, 
            cover_image_id=current_cover, 
            is_hidden=current_hidden, 
            password=body.password
        )
        return SuccessResponse(success=True, msg="Album updated successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False, error="Failed to Update Album", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id} - Delete an album
@router.delete("/{album_id}", response_model=SuccessResponse)
def delete_album(album_id: str = Path(...)):
    if not db_get_album(album_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    try:
        db_delete_album(album_id)
        return SuccessResponse(success=True, msg="Album deleted successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Delete Album", message=str(e)
            ).model_dump(),
        )


# GET /albums/{album_id}/media - Get all images/videos
@router.get("/{album_id}/media", response_model=GetAlbumMediaResponse)
def get_album_media(
    album_id: str = Path(...), 
    password: str = Query(None) # Fixed: Using Query param for GET request
):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Album Not Found", message="Album not found"
            ).model_dump(),
        )

    if album["is_hidden"]:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Password Required",
                    message="Password is required to access this hidden album.",
                ).model_dump(),
            )
        if not verify_album_password(album_id, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid Password",
                    message="The password provided is incorrect.",
                ).model_dump(),
            )

    try:
        media_items = db_get_album_media(album_id)
        return GetAlbumMediaResponse(success=True, media_items=media_items)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Retrieve Media", message=str(e)
            ).model_dump(),
        )


# POST /albums/{album_id}/media - Add images/videos
@router.post("/{album_id}/media", response_model=SuccessResponse)
def add_media_to_album(album_id: str = Path(...), body: AddMediaRequest = Body(...)):
    if not db_get_album(album_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    if not body.media_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="No Media Items",
                message="You must provide at least one item to add.",
            ).model_dump(),
        )

    try:
        items_to_add = [(item.media_id, item.media_type) for item in body.media_items]
        
        count = db_add_media_to_album(album_id, items_to_add)
        return SuccessResponse(
            success=True, msg=f"Added {count} items to album"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Add Media", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id}/media/{media_id} - Remove item
@router.delete("/{album_id}/media/{media_id}", response_model=SuccessResponse)
def remove_media_from_album(album_id: str = Path(...), media_id: str = Path(...)):
    if not db_get_album(album_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Album Not Found", message="Album not found"
            ).model_dump(),
        )

    try:
        db_remove_media_from_album(album_id, media_id)
        return SuccessResponse(
            success=True, msg="Media removed from album successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Remove Media", message=str(e)
            ).model_dump(),
        )