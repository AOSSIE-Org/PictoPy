from fastapi import APIRouter, HTTPException, status, Query, Body, Path
import uuid
from app.schemas.album import (
    GetAlbumsResponse,
    CreateAlbumRequest,
    CreateAlbumResponse,
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
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_add_images_to_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    verify_album_password,
)

router = APIRouter()


# GET /albums/ - Get all albums
@router.get("/", response_model=GetAlbumsResponse)
def get_albums(show_hidden: bool = Query(False)):
    albums = db_get_all_albums(show_hidden)
    album_list = []
    for album in albums:
        album_list.append(
            Album(
                album_id=album[0],
                album_name=album[1],
                description=album[2] or "",
                is_hidden=bool(album[3]),
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
        db_insert_album(album_id, body.name, body.description, body.is_hidden, body.password)
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
            detail=ErrorResponse(success=False, error="Album Not Found", message="Album not found").model_dump(),
        )

    try:
        album_obj = Album(
            album_id=album[0],
            album_name=album[1],
            description=album[2] or "",
            is_hidden=bool(album[3]),
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
        "is_hidden": bool(album[3]),
        "password_hash": album[4],
    }

    if album_dict["password_hash"]:
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
        db_update_album(album_id, body.name, body.description, body.is_hidden, body.password)
        return SuccessResponse(success=True, msg="Album updated successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(success=False, error="Failed to Update Album", message=str(e)).model_dump(),
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
            detail=ErrorResponse(success=False, error="Failed to Delete Album", message=str(e)).model_dump(),
        )


# GET /albums/{album_id}/images - Get all images in an album
@router.post("/{album_id}/images/get", response_model=GetAlbumImagesResponse)
# GET requests do not accept a body by default.
# Since we need to send a password securely, switching this to POST -- necessary.
# Open to suggestions if better approach possible.
def get_album_images(album_id: str = Path(...), body: GetAlbumImagesRequest = Body(...)):
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
        "is_hidden": bool(album[3]),
        "password_hash": album[4],
    }

    if album_dict["is_hidden"]:
        if not body.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Password Required",
                    message="Password is required to access this hidden album.",
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
            detail=ErrorResponse(success=False, error="Failed to Retrieve Images", message=str(e)).model_dump(),
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
        return SuccessResponse(success=True, msg=f"Added {len(body.image_ids)} images to album")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(success=False, error="Failed to Add Images", message=str(e)).model_dump(),
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
        return SuccessResponse(success=True, msg="Image removed from album successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(success=False, error="Failed to Remove Image", message=str(e)).model_dump(),
        )


# DELETE /albums/{album_id}/images - Remove multiple images from album
@router.delete("/{album_id}/images", response_model=SuccessResponse)
def remove_images_from_album(album_id: str = Path(...), body: ImageIdsRequest = Body(...)):
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
        return SuccessResponse(success=True, msg=f"Removed {len(body.image_ids)} images from album")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(success=False, error="Failed to Remove Images", message=str(e)).model_dump(),
        )
