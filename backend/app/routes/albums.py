import os
from fastapi import (
    APIRouter, status, 
    Query,Depends,
    HTTPException , 
)
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
from app.schemas.album import (
    AlbumCreate,AlbumCreateResponse,
    AlbumDeleteRequest,AlbumDeleteResponse,
    AddMultipleImagesRequest,AddMultipleImagesResponse,
    RemoveFromAlbumRequest,RemoveFromAlbumResponse,
    ViewAlbumRequest,ViewAlbumResponse,
    validate_view_album_request,ErrorResponse
)
from pydantic import ValidationError

router = APIRouter()

@router.post("/create-album",response_model=AlbumCreateResponse,responses={400: {"model": ErrorResponse}})
@exception_handler_wrapper
def create_new_album(payload:AlbumCreate):
    try:
        # Call the function to create an album
        create_album(payload.name, payload.description, payload.is_hidden, payload.password)
        # Success Response
        return AlbumCreateResponse(
            success=True,
            message=f"Album '{payload.name}' created successfully",
            data={
                "album_name": payload.name,
                "description": payload.description,
                "is_hidden": payload.is_hidden
            }
        )

    except ValidationError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": "Validation Error", "message": str(e)}
        )

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Server Error", "message": "An unexpected error occurred"}
        )



@router.delete("/delete-album",response_model=AlbumDeleteResponse)
@exception_handler_wrapper
def delete_existing_album(payload: AlbumDeleteRequest):
    
    album_name = payload.name 
    delete_album(album_name)
    try :
        return AlbumDeleteResponse(
            success=True,
            message=f"Album '{album_name}' deleted successfully",
            data=album_name
        )
    except Exception as e:

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=AlbumDeleteResponse(
                success=False,
                message="Failed to delete album",
                data=None
            ).dict()
        )



@router.post("/add-multiple-to-album",response_model=AddMultipleImagesResponse)
@exception_handler_wrapper
def add_multiple_images_to_album(payload: AddMultipleImagesRequest):
    
    album_name = payload.album_name
    paths = payload.paths 

    for path in paths : 
        try : 
            add_photo_to_album(album_name, path)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AddMultipleImagesResponse(
                    success=False,
                    message=f"Error adding image '{path}' to album '{album_name}'",
                    data={"error": str(e)}
                ).dict()
            )

    return AddMultipleImagesResponse(
        success=True,
        message=f"Images added to album '{album_name}' successfully",
        data={"album_name": album_name, "paths": paths}
    )




@router.delete("/remove-from-album", response_model=RemoveFromAlbumResponse)
@exception_handler_wrapper
def remove_image_from_album(payload: RemoveFromAlbumRequest):
    remove_photo_from_album(payload.album_name, payload.path)

    return RemoveFromAlbumResponse(
        success=True,
        message=f"Image '{payload.path}' removed from album '{payload.album_name}' successfully",
        data={"album_name": payload.album_name, "path": payload.path},
    )



@router.get("/view-album")
@exception_handler_wrapper
def view_album_photos(payload: ViewAlbumRequest = Depends(validate_view_album_request)):
    """Handles album photo retrieval with Pydantic validation."""
    photos = get_album_photos(payload.album_name, payload.password)

    if photos is None:
        return ViewAlbumResponse(
            success=False,
            message=f"Album '{payload.album_name}' does not exist",
            data=None
        )

    folder_path = os.path.abspath(IMAGES_PATH)
    return ViewAlbumResponse(
        success=True,
        message=f"Successfully retrieved photos for album '{payload.album_name}'",
        data={"album_name": payload.album_name, "photos": photos, "folder_path": folder_path}
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
