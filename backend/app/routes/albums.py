from fastapi import APIRouter, HTTPException, status
from app.database.albums import add_photo_to_album, delete_album, remove_photo_from_album, create_album, get_all_albums

router = APIRouter()

@router.post("/create-album")
def create_new_album(payload: dict):
    try:
        if 'name' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'name' in payload")

        album_name = payload['name']
        create_album(album_name)

        return {"message": f"Album '{album_name}' created successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/delete-album")
def delete_existing_album(payload: dict):
    try:
        if 'name' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'name' in payload")

        album_name = payload['name']
        delete_album(album_name)

        return {"message": f"Album '{album_name}' deleted successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/add-to-album")
def add_image_to_album(payload: dict):
    try:
        if 'album_name' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'album_name' in payload")
        if 'path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' in payload")

        album_name = payload['album_name']
        path = payload['path']

        add_photo_to_album(album_name, path)

        return {"message": f"Image '{path}' added to album '{album_name}' successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/remove-from-album")
def remove_image_from_album(payload: dict):
    try:
        if 'album_name' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'album_name' in payload")
        if 'path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' in payload")

        album_name = payload['album_name']
        path = payload['path']

        remove_photo_from_album(album_name, path)

        return {"message": f"Image '{path}' removed from album '{album_name}' successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/albums")
def get_albums():
    try:
        albums = get_all_albums()
        return {"albums": albums}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))