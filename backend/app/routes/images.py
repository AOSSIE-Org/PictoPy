import os
import shutil
from fastapi import APIRouter, HTTPException, status
from app.config.settings  import IMAGES_PATH
# from app.routes.test import 

router = APIRouter()


@router.get("/all-images")
def get_images():
    try:
        files = os.listdir(IMAGES_PATH)
        # for now include bmp and gif, could remove later
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] 
        image_files = [os.path.abspath(os.path.join(IMAGES_PATH, file)) for file in files if os.path.splitext(file)[1].lower() in image_extensions]
        
        return {"images": image_files}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    


@router.post("/single-image")
def add_single_image(payload: dict):
    try:
        if 'path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' in payload")

        image_path = payload['path']
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")

        # for now include bmp and gif, could remove later
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension not in image_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not an image")

        destination_path = os.path.join(IMAGES_PATH, os.path.basename(image_path))
        # if we do not want to store copies and just move use shutil.move instead
        shutil.copy(image_path, destination_path)

        return {"message": "Image copied to the gallery successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.delete("/delete-image")
def delete_image(payload: dict):
    try:
        if 'filename' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'filename' in payload")

        filename = payload['filename']
        file_path = os.path.join(IMAGES_PATH, filename)

        if not os.path.isfile(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")

        os.remove(file_path)

        return {"message": "Image deleted successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))