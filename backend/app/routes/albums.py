from fastapi import APIRouter, HTTPException, status, Query
from app.database.albums import (
    add_photo_to_album,
    delete_album,
    remove_photo_from_album,
    create_album,
    get_all_albums,
    add_photos_to_album,
    get_album_photos,
    edit_album_description,
)


"""
TODO:
1. Add album description (can be null and edited), date created, (add it for images as well?)
2. Add error checking, handle edge cases, throw mmore descriptive errors, currently no errors are shown
"""
router = APIRouter()


@router.post("/create-album")
def create_new_album(payload: dict):
    try:
        if "name" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'name' in payload",
            )

        album_name = payload["name"]
        description = payload.get("description")  # This will be None if not provided
        create_album(album_name, description)

        return {"message": f"Album '{album_name}' created successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/delete-album")
def delete_existing_album(payload: dict):
    try:
        if "name" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'name' in payload",
            )

        album_name = payload["name"]
        delete_album(album_name)

        return {"message": f"Album '{album_name}' deleted successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/add-multiple-to-album")
def add_multiple_images_to_album(payload: dict):
    try:
        if "album_name" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'album_name' in payload",
            )
        if "paths" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'paths' in payload",
            )

        album_name = payload["album_name"]
        paths = payload["paths"]

        if not isinstance(paths, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'paths' should be a list",
            )

        add_photos_to_album(album_name, paths)

        return {"message": f"Images added to album '{album_name}' successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/remove-from-album")
def remove_image_from_album(payload: dict):
    try:
        if "album_name" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'album_name' in payload",
            )
        if "path" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'path' in payload",
            )

        album_name = payload["album_name"]
        path = payload["path"]

        remove_photo_from_album(album_name, path)

        return {
            "message": f"Image '{path}' removed from album '{album_name}' successfully"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/view-album")
def view_album_photos(
    album_name: str = Query(..., description="Name of the album to view")
):
    try:
        if not album_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'album_name' parameter",
            )

        photos = get_album_photos(album_name)

        if photos is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album '{album_name}' not found",
            )

        return {"album_name": album_name, "photos": photos}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/edit-album-description")
def update_album_description(payload: dict):
    try:
        if "name" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'name' in payload",
            )
        if "description" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'description' in payload",
            )

        album_name = payload["name"]
        new_description = payload["description"]

        edit_album_description(album_name, new_description)

        return {"message": f"Description for album '{album_name}' updated successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/view-all")
def get_albums():
    try:
        albums = get_all_albums()
        return {"albums": albums}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
