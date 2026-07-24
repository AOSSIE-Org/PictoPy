import sqlite3
import uuid
from functools import wraps

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from app.database.albums import (
    db_add_images_to_album,
    db_delete_album,
    db_get_album,
    db_get_album_by_name,
    db_get_album_images,
    db_get_all_albums,
    db_insert_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    db_update_album,
    verify_album_password,
)
from app.logging.setup_logging import get_logger
from app.schemas.album import (
    Album,
    CreateAlbumRequest,
    CreateAlbumResponse,
    ErrorResponse,
    GetAlbumImagesRequest,
    GetAlbumImagesResponse,
    GetAlbumResponse,
    GetAlbumsResponse,
    ImageIdsRequest,
    SuccessResponse,
    UpdateAlbumRequest,
)

logger = get_logger(__name__)


def handle_route_exceptions(error_title: str, error_message: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error in {func.__name__} route: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponse(
                        success=False,
                        error=error_title,
                        message=error_message,
                    ).model_dump(),
                )

        return wrapper

    return decorator


router = APIRouter()

# GET /albums/ - Get all albums

router.get("/", response_model=GetAlbumsResponse)


@handle_route_exceptions(
    "Internal Server Error", "An unexpected error occurred while fetching albums."
)
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

router.post("/", response_model=CreateAlbumResponse)


@handle_route_exceptions(
    "Internal Server Error", "An unexpected error occurred while creating the album."
)
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
            album_id, body.name, body.description, body.is_hidden, body.password
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                success=False,
                error="Album Already Exists",
                message=f"Album '{body.name}' is already in the database.",
            ).model_dump(),
        )
    return CreateAlbumResponse(success=True, album_id=album_id)


# GET /albums/{album_id} - Get specific album details
router.get("/{album_id}", response_model=GetAlbumResponse)


@handle_route_exceptions(
    "Internal Server Error", "An unexpected error occurred while fetching the album."
)
def get_album(album_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Album Not Found", message="Album not found"
            ).model_dump(),
        )

    album_obj = Album(
        album_id=album[0],
        album_name=album[1],
        description=album[2] or "",
        is_hidden=bool(album[3]),
    )
    return GetAlbumResponse(success=True, data=album_obj)


# PUT /albums/{album_id} - Update Album

router.put("/{album_id}", response_model=SuccessResponse)


@handle_route_exceptions(
    "Failed to Update Album", "An unexpected error occurred while updating the album."
)
def update_album(
    album_id: str = Path(...), body: UpdateAlbumRequest = Body(...)
):  # noqa: B008
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

    db_update_album(
        album_id, body.name, body.description, body.is_hidden, body.password
    )
    return SuccessResponse(success=True, msg="Album updated successfully")


# DELETE /albums/{album_id} - Delete an album
router.delete("/{album_id}", response_model=SuccessResponse)


@handle_route_exceptions(
    "Failed to Delete Album", "An unexpected error occurred while deleting the album."
)
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

    db_delete_album(album_id)
    return SuccessResponse(success=True, msg="Album deleted successfully")


# GET /albums/{album_id}/images - Get all images in an album
router.post("/{album_id}/images/get", response_model=GetAlbumImagesResponse)


@handle_route_exceptions(
    "Failed to Retrieve Images", "An unexpected error occurred while retrieving images."
)
def get_album_images(
    album_id: str = Path(...), body: GetAlbumImagesRequest = Body(...)  # noqa: B008
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

    image_ids = db_get_album_images(album_id)
    return GetAlbumImagesResponse(success=True, image_ids=image_ids)


# POST /albums/{album_id}/images - Add images to an album

router.post("/{album_id}/images", response_model=SuccessResponse)


@handle_route_exceptions(
    "Failed to Add Images", "An unexpected error occurred while adding images."
)
def add_images_to_album(
    album_id: str = Path(...), body: ImageIdsRequest = Body(...)
):  # noqa: B008
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
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False, error="Invalid Image IDs", message=str(e)
            ).model_dump(),
        )

    return SuccessResponse(
        success=True, msg=f"Added {len(body.image_ids)} images to album"
    )


# DELETE /albums/{album_id}/images/{image_id} - Remove image from album

router.delete("/{album_id}/images/{image_id}", response_model=SuccessResponse)


@handle_route_exceptions(
    "Failed to Remove Image", "An unexpected error occurred while removing the image."
)
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Image Not Found", message=str(e)
            ).model_dump(),
        )

    return SuccessResponse(success=True, msg="Image removed from album successfully")


# DELETE /albums/{album_id}/images - Remove multiple images from album

router.delete("/{album_id}/images", response_model=SuccessResponse)


@handle_route_exceptions(
    "Failed to Remove Images", "An unexpected error occurred while removing the images."
)
def remove_images_from_album(
    album_id: str = Path(...), body: ImageIdsRequest = Body(...)  # noqa: B008
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

    db_remove_images_from_album(album_id, body.image_ids)
    return SuccessResponse(
        success=True, msg=f"Removed {len(body.image_ids)} images from album"
    )
