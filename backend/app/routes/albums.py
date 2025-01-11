import os
from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from app.database.albums import (
    add_photo_to_album,
    delete_album,
    remove_photo_from_album,
    create_album,
    get_all_albums,
    get_album_photos,
    edit_album_description,
)
from app.utils.APIError import APIError
from app.utils.wrappers import exception_handler_wrapper
from app.config.settings import IMAGES_PATH

router = APIRouter()


@router.post("/create-album")
@exception_handler_wrapper
def create_new_album(payload: dict):
    if "name" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'name' in payload",
                    "message": "Album name is required",
                },
            },
        )
    album_name = payload["name"]
    description = payload.get("description")
    create_album(album_name, description)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "data": {"album_name": album_name, "description": description},
            "message": f"Album '{album_name}' created successfully",
            "success": True,
        },
    )


@router.delete("/delete-album")
@exception_handler_wrapper
def delete_existing_album(payload: dict):
    if "name" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'name' in payload",
                    "message": "Album name is required",
                },
            },
        )

    album_name = payload["name"]
    delete_album(album_name)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": album_name,
            "message": f"Album '{album_name}' deleted successfully",
            "success": True,
        },
    )


@router.post("/add-multiple-to-album")
@exception_handler_wrapper
def add_multiple_images_to_album(payload: dict):
    if "album_name" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'album_name' in payload",
                    "message": "Album name is required",
                },
            },
        )
    if "paths" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'paths' in payload",
                    "message": "Image paths are required",
                },
            },
        )

    album_name = payload["album_name"]
    paths = payload["paths"]

    if not isinstance(paths, list):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Invalid 'paths' format",
                    "message": "Paths should be a list",
                },
            },
        )

    for path in paths:
        try:
            add_photo_to_album(album_name, path)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "content": {
                        "success": False,
                        "error": f"Error adding image '{path}' to album '{album_name}'",
                        "message": str(e),
                    },
                },
            )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "data": {"album_name": album_name, "paths": paths},
            "message": f"Images added to album '{album_name}' successfully",
            "success": True,
        },
    )


@router.delete("/remove-from-album")
@exception_handler_wrapper
def remove_image_from_album(payload: dict):
    if "album_name" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'album_name' in payload",
                    "message": "Album name is required",
                },
            },
        )
    if "path" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'path' in payload",
                    "message": "Image path is required",
                },
            },
        )
    album_name = payload["album_name"]
    path = payload["path"]

    remove_photo_from_album(album_name, path)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": {"album_name": album_name, "path": path},
            "message": f"Image '{path}' removed from album '{album_name}' successfully",
            "success": True,
        },
    )


@router.get("/view-album")
@exception_handler_wrapper
def view_album_photos(
    album_name: str = Query(..., description="Name of the album to view"),
):
    if not album_name:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing album_name parameter",
                    "message": "Album name is required",
                },
            },
        )

    photos = get_album_photos(album_name)

    if photos is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status_code": status.HTTP_404_NOT_FOUND,
                "content": {
                    "success": False,
                    "error": f"Album '{album_name}' does not exist",
                    "message": "Album not found",
                },
            },
        )

    folder_path = os.path.abspath(IMAGES_PATH)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": {
                "album_name": album_name,
                "photos": photos,
                "folder_path": folder_path,
            },
            "message": f"Successfully retrieved photos for album '{album_name}'",
            "success": True,
        },
    )


@router.put("/edit-album-description")
@exception_handler_wrapper
def update_album_description(payload: dict):
    if "album_name" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'album_name' in payload",
                    "message": "Album name is required",
                },
            },
        )
    if "description" not in payload:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "content": {
                    "success": False,
                    "error": "Missing 'description' in payload",
                    "message": "New description is required",
                },
            },
        )

    album_name = payload["album_name"]
    new_description = payload["description"]

    edit_album_description(album_name, new_description)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": {"album_name": album_name, "new_description": new_description},
            "message": f"Description for album '{album_name}' updated successfully",
            "success": True,
        },
    )


@router.get("/view-all")
@exception_handler_wrapper
def get_albums():
    albums = get_all_albums()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": albums,
            "message": "Successfully retrieved all albums",
            "success": True,
        },
    )
