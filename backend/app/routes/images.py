import os
import shutil
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.config.settings import IMAGES_PATH
from app.facenet.facenet import detect_faces
from app.utils.classification import get_classes
from app.database.images import (
    get_all_image_ids_from_db,
    get_path_from_id,
    insert_image_db,
    delete_image_db,
    get_objects_db,
    extract_metadata,
)

router = APIRouter()

async def run_get_classes(img_path):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path))
    if result:
        classes = result.split(",")
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)

@router.get("/all-images")
def get_images():
    try:
        files = os.listdir(IMAGES_PATH)
        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        image_files = [
            os.path.abspath(os.path.join(IMAGES_PATH, file))
            for file in files
            if os.path.splitext(file)[1].lower() in image_extensions
        ]

        return JSONResponse(
            status_code=200,
            content={
                "data": image_files,
                "message": "Successfully retrieved all images",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.post("/images")
async def add_multiple_images(payload: dict):
    try:
        if "paths" not in payload:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Missing 'paths' in payload",
                        "message": "Image paths are required"
                    }
                }
            )

        image_paths = payload["paths"]
        if not isinstance(image_paths, list):
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Invalid 'paths' format",
                        "message": "'paths' should be a list"
                    }
                }
            )

        tasks = []
        for image_path in image_paths:
            if not os.path.isfile(image_path):
                return JSONResponse(
                    status_code=400,
                    content={
                        "status_code": 400,
                        "content": {
                            "success": False,
                            "error": "Invalid file path",
                            "message": f"Invalid file path: {image_path}"
                        }
                    }
                )

            image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
            file_extension = os.path.splitext(image_path)[1].lower()
            if file_extension not in image_extensions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status_code": 400,
                        "content": {
                            "success": False,
                            "error": "Invalid file type",
                            "message": f"File is not an image: {image_path}"
                        }
                    }
                )

            destination_path = os.path.join(IMAGES_PATH, os.path.basename(image_path))
            shutil.copy(image_path, destination_path)
            tasks.append(asyncio.create_task(run_get_classes(destination_path)))

        asyncio.create_task(process_images(tasks))

        return JSONResponse(
            status_code=202,
            content={
                "data": len(tasks),
                "message": "Images are being processed in the background",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

async def process_images(tasks):
    await asyncio.gather(*tasks)

@router.delete("/delete-image")
def delete_image(payload: dict):
    try:
        if "path" not in payload:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Missing 'path' in payload",
                        "message": "Image path is required"
                    }
                }
            )

        filename = payload["path"]
        file_path = os.path.join(IMAGES_PATH, filename)

        if not os.path.isfile(file_path):
            return JSONResponse(
                status_code=404,
                content={
                    "status_code": 404,
                    "content": {
                        "success": False,
                        "error": "Image not found",
                        "message": "Image file not found"
                    }
                }
            )

        os.remove(file_path)
        delete_image_db(file_path)
        return JSONResponse(
            status_code=200,
            content={
                "data": file_path,
                "message": "Image deleted successfully",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.delete("/multiple-images")
def delete_multiple_images(payload: dict):
    try:
        paths = payload["paths"]
        if not isinstance(paths, list):
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Invalid 'paths' format",
                        "message": "'paths' should be a list"
                    }
                }
            )

        deleted_paths = []
        for path in paths:
            if not os.path.isfile(path):
                return JSONResponse(
                    status_code=404,
                    content={
                        "status_code": 404,
                        "content": {
                            "success": False,
                            "error": "Image not found",
                            "message": f"Image file not found: {path}"
                        }
                    }
                )

            os.remove(path)
            delete_image_db(path)
            deleted_paths.append(path)

        return JSONResponse(
            status_code=200,
            content={
                "data": deleted_paths,
                "message": "Images deleted successfully",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.get("/all-image-objects")
def get_all_image_objects():
    try:
        image_ids = get_all_image_ids_from_db()

        data = {}
        for image_id in image_ids:
            image_path = get_path_from_id(image_id)
            classes = get_objects_db(image_path)
            data[image_path] = classes if classes else "None"

        return JSONResponse(
            status_code=200,
            content={
                "data": data,
                "message": "Successfully retrieved all image objects",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.get("/class-ids")
def get_class_ids(path: str = Query(...)):
    try:
        if not path:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Missing 'path' parameter",
                        "message": "Image path is required"
                    }
                }
            )

        class_ids = get_objects_db(path)
        if not class_ids:
            return JSONResponse(
                status_code=200,
                content={
                    "data": {"class_ids": "None"},
                    "message": "No class IDs found for the image",
                    "success": True
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "data": class_ids,
                "message": "Successfully retrieved class IDs",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.post("/add-folder")
async def add_folder(payload: dict):
    try:
        if "folder_path" not in payload:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Missing 'folder_path' in payload",
                        "message": "Folder path is required"
                    }
                }
            )

        folder_path = payload["folder_path"]
        if not os.path.isdir(folder_path):
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content": {
                        "success": False,
                        "error": "Invalid folder path",
                        "message": "The provided path is not a valid directory"
                    }
                }
            )

        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        tasks = []

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension in image_extensions:
                    destination_path = os.path.join(IMAGES_PATH, file)

                    if os.path.exists(destination_path):
                        continue

                    shutil.copy(file_path, destination_path)
                    tasks.append(asyncio.create_task(run_get_classes(destination_path)))

        if not tasks:
            return JSONResponse(
                status_code=200,
                content={
                    "data": 0,
                    "message": "No valid images found in the specified folder",
                    "success": True
                }
            )

        await asyncio.create_task(process_images(tasks))

        return JSONResponse(
            status_code=200,
            content={
                "data": len(tasks),
                "message": f"Processing {len(tasks)} images from the folder in the background",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )