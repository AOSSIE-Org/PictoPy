from fastapi import APIRouter, HTTPException, status, Body, Path
import sqlite3
import uuid
from app.schemas.album import (
    GetAlbumsResponse,
    CreateAlbumRequest,
    CreateAlbumResponse,
    CreateAlbumFromMemoryData,
    CreateAlbumFromMemoryRequest,
    CreateAlbumFromMemoryResponse,
    GetAlbumResponse,
    GetAlbumImagesRequest,
    GetAlbumImagesResponse,
    UpdateAlbumRequest,
    SuccessResponse,
    ErrorResponse,
    ImageIdsRequest,
    Album,
)
from app.database.albums import (
    db_get_all_albums,
    db_get_album_by_name,
    db_get_album,
    db_insert_album,
    db_create_album_with_images,
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_add_images_to_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    db_get_album_cover_path,
    verify_album_password,
)
from app.database.memories import db_get_memory, db_get_memory_images

router = APIRouter()


# GET /albums/ - Get all albums (including locked ones)
@router.get("/", response_model=GetAlbumsResponse)
def get_albums():
    """Get all albums. Always returns both locked and unlocked albums."""
    albums = db_get_all_albums()
    album_list = []
    for album in albums:
        # Get image count for each album
        image_ids = db_get_album_images(album[0])
        image_count = len(image_ids)
        is_locked = bool(album[3])

        album_list.append(
            Album(
                album_id=album[0],
                album_name=album[1],
                description=album[2] or "",
                is_locked=is_locked,
                # A locked album's cover would show the very content the
                # password is protecting, so never send it.
                cover_image_path=(
                    None if is_locked else db_get_album_cover_path(album[0])
                ),
                image_count=image_count,
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
        db_insert_album(
            album_id, body.name, body.description, body.is_locked, body.password
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


# POST /albums/from-memory - Create an album from a curated memory
@router.post("/from-memory", response_model=CreateAlbumFromMemoryResponse)
def create_album_from_memory(body: CreateAlbumFromMemoryRequest = Body(...)):
    """
    Copy a memory's photos into a new album.

    The memory itself is left untouched, so the same one can be converted
    again under a different name. Any clips are left behind: album_images
    references images, and albums have no video support.
    """
    memory = db_get_memory(body.memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Memory Not Found",
                message="No memory exists with the provided ID.",
            ).model_dump(),
        )

    image_ids = [image["id"] for image in db_get_memory_images(body.memory_id)]
    if not image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Empty Memory",
                message="This memory has no photos to convert.",
            ).model_dump(),
        )

    if db_get_album_by_name(body.name):
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
        image_count = db_create_album_with_images(
            album_id, body.name, memory.get("subtitle") or "", image_ids
        )
    except sqlite3.IntegrityError as e:
        # The name check above is not atomic. Re-check rather than assume a
        # conflict: the same error covers an image that vanished mid-request.
        if db_get_album_by_name(body.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    success=False,
                    error="Album Already Exists",
                    message=f"Album '{body.name}' is already in the database.",
                ).model_dump(),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Failed to create album from memory: {str(e)}",
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Failed to create album from memory: {str(e)}",
            ).model_dump(),
        )

    return CreateAlbumFromMemoryResponse(
        success=True,
        message=f"Created album '{body.name}' with {image_count} photos",
        data=CreateAlbumFromMemoryData(album_id=album_id, image_count=image_count),
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
        # Get image count for the album
        image_ids = db_get_album_images(album_id)
        image_count = len(image_ids)

        is_locked = bool(album[3])
        album_obj = Album(
            album_id=album[0],
            album_name=album[1],
            description=album[2] or "",
            is_locked=is_locked,
            # Same reasoning as the listing: the cover gives away the contents.
            cover_image_path=(None if is_locked else db_get_album_cover_path(album_id)),
            image_count=image_count,
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

    album_dict = {
        "album_id": album[0],
        "album_name": album[1],
        "description": album[2],
        "is_locked": bool(album[3]),
        "password_hash": album[4],
    }

    if album_dict["is_locked"]:
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
        db_update_album(
            album_id, body.name, body.description, body.is_locked, body.password
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
    album = db_get_album(album_id)
    if not album:
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


# GET /albums/{album_id}/images - Get all images in an album
@router.post("/{album_id}/images/get", response_model=GetAlbumImagesResponse)
# GET requests do not accept a body by default.
# Since we need to send a password securely, switching this to POST -- necessary.
# Open to suggestions if better approach possible.
def get_album_images(
    album_id: str = Path(...), body: GetAlbumImagesRequest = Body(...)
):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    album_dict = {
        "album_id": album[0],
        "album_name": album[1],
        "description": album[2],
        "is_locked": bool(album[3]),
        "password_hash": album[4],
    }

    if album_dict["is_locked"]:
        if not body.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Password Required",
                    message="Password is required to access this locked album.",
                ).model_dump(),
            )
        if not verify_album_password(album_id, body.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid Password",
                    message="The password provided is incorrect.",
                ).model_dump(),
            )

    try:
        image_ids = db_get_album_images(album_id)
        return GetAlbumImagesResponse(success=True, image_ids=image_ids)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Retrieve Images", message=str(e)
            ).model_dump(),
        )


# POST /albums/{album_id}/images - Add images to an album
@router.post("/{album_id}/images", response_model=SuccessResponse)
def add_images_to_album(album_id: str = Path(...), body: ImageIdsRequest = Body(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    if not body.image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="No Image IDs",
                message="You must provide a list of image IDs to add.",
            ).model_dump(),
        )

    try:
        db_add_images_to_album(album_id, body.image_ids)
        return SuccessResponse(
            success=True, msg=f"Added {len(body.image_ids)} images to album"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Add Images", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id}/images/{image_id} - Remove image from album
@router.delete("/{album_id}/images/{image_id}", response_model=SuccessResponse)
def remove_image_from_album(album_id: str = Path(...), image_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    try:
        db_remove_image_from_album(album_id, image_id)
        return SuccessResponse(
            success=True, msg="Image removed from album successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Remove Image", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id}/images - Remove multiple images from album
@router.delete("/{album_id}/images", response_model=SuccessResponse)
def remove_images_from_album(
    album_id: str = Path(...), body: ImageIdsRequest = Body(...)
):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Album Not Found",
                message="No album exists with the provided ID.",
            ).model_dump(),
        )

    if not body.image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="No Image IDs Provided",
                message="You must provide at least one image ID to remove.",
            ).model_dump(),
        )

    try:
        db_remove_images_from_album(album_id, body.image_ids)
        return SuccessResponse(
            success=True, msg=f"Removed {len(body.image_ids)} images from album"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Failed to Remove Images", message=str(e)
            ).model_dump(),
        )
