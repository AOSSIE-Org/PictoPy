from fastapi import APIRouter, HTTPException, status, Body, Path
import uuid

from typing import Callable, TypeVar
from typing_extensions import ParamSpec
from functools import wraps
import sqlite3
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

def handle_route_exceptions(error_title: str, error_message: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
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

from app.schemas.album import (
    GetAlbumsResponse,
    CreateAlbumRequest,
    CreateAlbumResponse,
    CreateAlbumFromMemoryData,
    CreateAlbumFromMemoryRequest,
    CreateAlbumFromMemoryResponse,
    ErrorResponseEnvelope,
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
    db_get_album_cover_path,
    verify_album_password,
)
from app.utils.albums import (
    AlbumNameTakenError,
    MemoryHasNoPhotosError,
    MemoryNotFoundError,
    album_util_create_from_memory,
)

router = APIRouter()


def _album_exists(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorResponse(
            success=False,
            error="Album Already Exists",
            message=f"Album '{name}' is already in the database.",
        ).model_dump(),
    )


def _internal_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorResponse(
            success=False, error="Internal Server Error", message=message
        ).model_dump(),
    )


# GET /albums/ - Get all albums (including locked ones)
@router.get("/", response_model=GetAlbumsResponse)
@handle_route_exceptions("Internal Server Error", "An unexpected error occurred while fetching albums.")
def get_albums():
    """Get all albums. Always returns both locked and unlocked albums."""
    albums = db_get_all_albums()
    album_list = []
    for album in albums:
        # Get image count for each album
        image_ids = db_get_album_images(album["album_id"])
        image_count = len(image_ids)
        is_locked = album["is_locked"]

        album_list.append(
            Album(
                album_id=album["album_id"],
                album_name=album["album_name"],
                description=album["description"] or "",
                is_locked=is_locked,
                # A locked album's cover would show the very content the
                # password is protecting, so never send it.
                cover_image_path=(
                    None if is_locked else db_get_album_cover_path(album["album_id"])
                ),
                image_count=image_count,
                created_at=album["created_at"],
                updated_at=album["updated_at"],
            )
        )
    return GetAlbumsResponse(success=True, albums=album_list)


# POST /albums/ - Create a new album
@router.post("/", response_model=CreateAlbumResponse)
@handle_route_exceptions("Internal Server Error", "An unexpected error occurred while creating the album.")
def create_album(body: CreateAlbumRequest):
    existing_album = db_get_album_by_name(body.name)
    if existing_album:
        raise _album_exists(body.name)

    album_id = str(uuid.uuid4())
    try:
        db_insert_album(
            album_id, body.name, body.description, body.is_locked, body.password
        )
        return CreateAlbumResponse(success=True, album_id=album_id)
    except sqlite3.IntegrityError:
        raise _album_exists(body.name)


# POST /albums/from-memory - Create an album from a curated memory
@router.post(
    "/from-memory",
    response_model=CreateAlbumFromMemoryResponse,
    responses={code: {"model": ErrorResponseEnvelope} for code in [400, 404, 409, 500]},
)
def create_album_from_memory(
    body: CreateAlbumFromMemoryRequest,
) -> CreateAlbumFromMemoryResponse:
    """
    Copy a memory's photos into a new album.

    The memory itself is left untouched, so the same one can be converted
    again under a different name. Any clips are left behind: album_images
    references images, and albums have no video support.
    """
    try:
        result = album_util_create_from_memory(body.memory_id, body.name)
    except MemoryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Memory Not Found",
                message="No memory exists with the provided ID.",
            ).model_dump(),
        ) from e
    except MemoryHasNoPhotosError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Empty Memory",
                message="This memory has no photos to convert.",
            ).model_dump(),
        ) from e
    except AlbumNameTakenError as e:
        raise _album_exists(body.name) from e


    return CreateAlbumFromMemoryResponse(
        success=True,
        message=f"Created album '{body.name}' with {result['image_count']} photos",
        data=CreateAlbumFromMemoryData(**result),
    )


# GET /albums/{album_id} - Get specific album details
@router.get("/{album_id}", response_model=GetAlbumResponse)
@handle_route_exceptions("Internal Server Error", "An unexpected error occurred while fetching the album.")
def get_album(album_id: str = Path(...)):
    album = db_get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Album Not Found", message="Album not found"
            ).model_dump(),
        )

    # Get image count for the album
    image_ids = db_get_album_images(album_id)
    image_count = len(image_ids)

    is_locked = album["is_locked"]
    album_obj = Album(
        album_id=album["album_id"],
        album_name=album["album_name"],
        description=album["description"] or "",
        is_locked=is_locked,
        cover_image_path=(None if is_locked else db_get_album_cover_path(album_id)),
        image_count=image_count,
        created_at=album["created_at"],
        updated_at=album["updated_at"],
    )
    return GetAlbumResponse(success=True, data=album_obj)


# PUT /albums/{album_id} - Update Album
@router.put("/{album_id}", response_model=SuccessResponse)
@handle_route_exceptions("Failed to Update Album", "An unexpected error occurred while updating the album.")
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

    if album["is_locked"]:
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
    except sqlite3.IntegrityError:
        raise _album_exists(body.name)


# DELETE /albums/{album_id} - Delete an album
@router.delete("/{album_id}", response_model=SuccessResponse)
@handle_route_exceptions("Failed to Delete Album", "An unexpected error occurred while deleting the album.")
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
@router.post("/{album_id}/images/get", response_model=GetAlbumImagesResponse)
@handle_route_exceptions("Failed to Retrieve Images", "An unexpected error occurred while retrieving images.")
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

    if album["is_locked"]:
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

    image_ids = db_get_album_images(album_id)
    return GetAlbumImagesResponse(success=True, image_ids=image_ids)


# POST /albums/{album_id}/images - Add images to an album
@router.post("/{album_id}/images", response_model=SuccessResponse)
@handle_route_exceptions("Failed to Add Images", "An unexpected error occurred while adding images.")
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
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False, error="Failed to Add Images", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id}/images/{image_id} - Remove image from album
@router.delete("/{album_id}/images/{image_id}", response_model=SuccessResponse)
@handle_route_exceptions("Failed to Remove Image", "An unexpected error occurred while removing the image.")
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False, error="Failed to Remove Image", message=str(e)
            ).model_dump(),
        )


# DELETE /albums/{album_id}/images - Remove multiple images from album
@router.delete("/{album_id}/images", response_model=SuccessResponse)
@handle_route_exceptions("Failed to Remove Images", "An unexpected error occurred while removing the images.")
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

    db_remove_images_from_album(album_id, body.image_ids)
    return SuccessResponse(
        success=True, msg=f"Removed {len(body.image_ids)} images from album"
    )
