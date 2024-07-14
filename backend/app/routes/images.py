import os
import shutil
import asyncio
from fastapi import APIRouter, HTTPException, status, Query

from app.config.settings  import IMAGES_PATH
from app.utils.classification import get_classes
from app.database.images import get_all_image_ids_from_db, get_path_from_id, insert_image_db, delete_image_db, get_objects_db, extract_metadata

router = APIRouter()

async def run_get_classes(img_path):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    # error check here later
    insert_image_db(img_path, result, extract_metadata(img_path))


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
async def add_single_image(payload: dict):
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
        asyncio.create_task(run_get_classes(destination_path))

        return {"message": "Image copied to the gallery successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.post("/multiple-images")
async def add_multiple_images(payload: dict):
    try:
        if 'paths' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'paths' in payload")

        image_paths = payload['paths']
        if not isinstance(image_paths, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'paths' should be a list")

        tasks = []
        for image_path in image_paths:
            if not os.path.isfile(image_path):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file path: {image_path}")

            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            file_extension = os.path.splitext(image_path)[1].lower()
            if file_extension not in image_extensions:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File is not an image: {image_path}")

            destination_path = os.path.join(IMAGES_PATH, os.path.basename(image_path))
            shutil.copy(image_path, destination_path)
            tasks.append(asyncio.create_task(run_get_classes(destination_path)))

        # process all these asynchronously in the backend TODO ? add progress bar?
        asyncio.create_task(process_images(tasks))

        return {"message": "Images are being processed in the background"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def process_images(tasks):
    await asyncio.gather(*tasks)


@router.delete("/delete-image")
def delete_image(payload: dict):
    try:
        if 'path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' in payload")

        filename = payload['path']
        file_path = os.path.join(IMAGES_PATH, filename)

        if not os.path.isfile(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")

        os.remove(file_path)
        delete_image_db(file_path)
        return {"message": "Image deleted successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/all-image-objects")
def get_all_image_objects():
    try:
        image_ids = get_all_image_ids_from_db()
        
        data = {}
        for image_id in image_ids:
            image_path = get_path_from_id(image_id)
            classes = get_objects_db(image_path)
            print(image_path, classes, flush=True)
            if classes:
                data[image_path] = classes
            else:
                data[image_path] = "None"

        return {"data": data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def get_class_ids(path: str = Query(...)):
    try:
        if not path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' parameter")

        class_ids = get_objects_db(path)
        print(class_ids, flush=True)
        if not class_ids:
            return {"classes": "None"}

        if class_ids:
            #  ids = (",").join([class_names[int(x)] for x in list(set(class_ids[1:-1].split(" ")))])
            ids = class_ids
            return {"classes": ids}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found in the database")

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/add-folder")
async def add_folder(payload: dict):
    try:
        if 'folder_path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'folder_path' in payload")

        folder_path = payload['folder_path']
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid folder path")

        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        tasks = []

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                print(file_path)
                if file_extension in image_extensions:
                    destination_path = os.path.join(IMAGES_PATH, file)
                    
                    if os.path.exists(destination_path):
                        print(f"File {file} already exists in destination. Skipping.")
                        continue
                    
                    shutil.copy(file_path, destination_path)
                    tasks.append(asyncio.create_task(run_get_classes(destination_path)))

        if not tasks:
            return {"message": "No valid images found in the specified folder"}

        asyncio.create_task(process_images(tasks))

        return {"message": f"Processing {len(tasks)} images from the folder in the background"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
