import os
from fastapi import APIRouter, status, Query, HTTPException
from app.database.albums import (
    add_photo_to_album,
    delete_album,
    remove_photo_from_album,
    create_album,
    get_all_albums,
    get_album_photos,
    edit_album_description,
)
from app.utils.wrappers import exception_handler_wrapper
from app.config.settings import IMAGES_PATH
from app.schemas.album import (
    AlbumCreate,
    AlbumCreateResponse,
    AlbumDeleteResponse,
    AlbumDeleteRequest,
    AddMultipleImagesRequest,
    AddMultipleImagesResponse,
    RemoveImagFromAlbumRequest,
    RemoveImagFromAlbumResponse,
    ViewAlbumResponse,
    UpdateAlbumDescriptionRequest,
    UpdateAlbumDescriptionResponse,
    GetAlbumsResponse,
    ErrorResponse,
)


router = APIRouter()


@router.post("/create-album", response_model=AlbumCreateResponse)
@exception_handler_wrapper
def create_new_album(payload: AlbumCreate):
    # Call the function to create an album
    create_album(payload.name, payload.description, payload.is_hidden, payload.password)
    # Success Response
    return AlbumCreateResponse(
        success=True,
        message=f"Album '{payload.name}' created successfully",
        data={
            "album_name": payload.name,
            "description": payload.description,
            "is_hidden": payload.is_hidden,
        },
    )


@router.delete(
    "/delete-album",
    response_model=AlbumDeleteResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def delete_existing_album(payload: AlbumDeleteRequest):

    album_name = payload.name
    try:
        delete_album(album_name)
        return AlbumDeleteResponse(
            success=True,
            message=f"Album '{album_name}' deleted successfully",
            data=album_name,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Server Error", message="Failed to delete album"
            ).model_dump(),  #  # Convert Pydantic model to a dict
        )


@router.post(
    "/add-multiple-to-album",
    response_model=AddMultipleImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def add_multiple_images_to_album(payload: AddMultipleImagesRequest):

    album_name = payload.album_name
    paths = payload.paths

    for path in paths:
        try:
            add_photo_to_album(album_name, path)
        except Exception as e:

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    message=f"Error adding image '{path}' to album '{album_name}'",
                    error=str(e),
                ).model_dump(),
            )

    return AddMultipleImagesResponse(
        success=True,
        message=f"Images added to album '{album_name}' successfully",
        data={"album_name": album_name, "paths": paths},
    )


@router.delete(
    "/remove-from-album",
    response_model=RemoveImagFromAlbumResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def remove_image_from_album(payload: RemoveImagFromAlbumRequest):
    album_name = payload.album_name
    path = payload.path
    try:
        remove_photo_from_album(album_name, path)
        return RemoveImagFromAlbumResponse(
            data={"album_name": album_name, "path": path},
            message=f"Image '{path}' removed from album '{album_name}' successfully",
            success=True,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Internal server Error",
                error="Failed to remove photo from Album",
            ).model_dump(),
        )


@router.get(
    "/view-album",
    response_model=ViewAlbumResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404]},
)
@exception_handler_wrapper
def view_album_photos(
    album_name: str = Query(..., description="Name of the album to view"),
    password: str = Query(None, description="Password for hidden albums"),
):

    photos = get_album_photos(album_name, password)

    if photos is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error=f"Album '{album_name}' does not exist",
                message="Album not found",
            ).model_dump(),
        )

    folder_path = os.path.abspath(IMAGES_PATH)

    return ViewAlbumResponse(
        success=True,
        message=f"Successfully retrieved photos for album '{album_name}'",
        data={
            "album_name": album_name,
            "photos": photos if photos else [],
            "folder_path": folder_path,
        },
    )


@router.put(
    "/edit-album-description",
    response_model=UpdateAlbumDescriptionResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def update_album_description(payload: UpdateAlbumDescriptionRequest):

    album_name = payload.album_name
    new_description = payload.description

    try:
        edit_album_description(album_name, new_description)
        return UpdateAlbumDescriptionResponse(
            data={"album_name": album_name, "new_description": new_description},
            message=f"Description for album '{album_name}' updated successfully",
            success=True,
        )
    except Exception:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, message="Server error", error="Failed to update Album"
            ).model_dump(),
        )


@router.get(
    "/view-all",
    response_model=GetAlbumsResponse,
    responses={code: {"model": ErrorResponse} for code in [404]},
)
@exception_handler_wrapper
def get_albums():
    try:
        albums = get_all_albums()
        return GetAlbumsResponse(
            data=albums, message="Successfully retrieved all albums", success=True
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, message="Server error", error="Failed to update Album"
            ).model_dump(),
        )
