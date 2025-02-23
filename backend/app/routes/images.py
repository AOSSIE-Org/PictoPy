import os
import shutil
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from PIL import Image

# hello
from app.config.settings import IMAGES_PATH
from app.facenet.facenet import detect_faces
from app.utils.classification import get_classes
from app.utils.wrappers import exception_handler_wrapper
from app.database.images import (
    get_all_image_ids_from_db,
    get_path_from_id,
    insert_image_db,
    delete_image_db,
    get_objects_db,
    extract_metadata,
)

from app.schemas.images import (
    DeleteImageRequest,DeleteImageResponse,
    DeleteMultipleImagesRequest,DeleteMultipleImagesResponse,
    GetAllImageObjectsResponse,ErrorResponse,
    ClassIDsResponse,
    AddFolderRequest,AddFolderResponse,
    GenerateThumbnailsRequest,GenerateThumbnailsResponse,
    FailedPathResponse,ClassIDsResponse
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
                "data": {
                    "image_files": image_files,
                    "folder_path": os.path.abspath(IMAGES_PATH),
                },
                "message": "Successfully retrieved all images",
                "success": True,
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e),
                },
            },
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
                        "message": "Image paths are required",
                    },
                },
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
                        "message": "'paths' should be a list",
                    },
                },
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
                            "message": f"Invalid file path: {image_path}",
                        },
                    },
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
                            "message": f"File is not an image: {image_path}",
                        },
                    },
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
                "success": True,
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e),
                },
            },
        )


async def process_images(tasks):
    await asyncio.gather(*tasks)


@router.delete("/delete-image",response_model=DeleteImageResponse)
def delete_image(payload: DeleteImageRequest):
    try:
        
        filename = payload.path
        file_path = os.path.join(IMAGES_PATH, filename)

        if not os.path.isfile(file_path):
            return JSONResponse(
                status_code=404,
                content={
                    "status_code": 404,
                    "content": ErrorResponse(
                        success=False,
                        error="Image not found",
                        message="Image file not found"
                    ),
                },
            )

        os.remove(file_path)
        delete_image_db(file_path)
        return DeleteImageResponse(
            data=file_path,
            message="Image deleted successfully",
            success=True
         )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e),
                )
            },
        )


@router.delete("/multiple-images",response_model=DeleteMultipleImagesResponse)
def delete_multiple_images(payload: DeleteMultipleImagesRequest):
    try:
        paths = payload.paths
        deleted_paths = []
        for path in paths:
            if not os.path.isfile(path):
                return JSONResponse(
                    status_code=404,
                    content={
                        "status_code": 404,
                        "content": ErrorResponse(
                            success=False,
                            error="Image not found",
                            message=f"Image file not found: {path}",
                        )
                    },
                )
            path = os.path.normpath(path)
            folder_path, filename = os.path.split(path)
            thumbnail_folder = os.path.join(folder_path, "PictoPy.thumbnails")
            thumb_nail_image_path = os.path.join(thumbnail_folder, filename)

            # Check and remove the original file
            if os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    print(f"Permission denied for file '{path}'.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                print(f"File '{path}' does not exist.")

            # Check and remove the thumbnail file
            if os.path.exists(thumb_nail_image_path):
                try:
                    os.remove(thumb_nail_image_path)
                except PermissionError:
                    print(f"Permission denied for file '{thumb_nail_image_path}'.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                print(f"File '{thumb_nail_image_path}' does not exist.")

            delete_image_db(path)
            deleted_paths.append(path)
        
        return DeleteMultipleImagesResponse(
            data=deleted_paths,
            message="Images deleted successfully",
            success=True
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content" : ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e),
                )
            },
        )


@router.get("/all-image-objects",response_model=GetAllImageObjectsResponse)
def get_all_image_objects():
    try:
        folder_path = os.path.abspath(IMAGES_PATH)
        print(folder_path)
        image_ids = get_all_image_ids_from_db()
        data = {}
        for image_id in image_ids:
            image_path = get_path_from_id(image_id)
            classes = get_objects_db(image_path)
            data[image_path] = classes if classes else "None"
            print(image_path)
        
        return GetAllImageObjectsResponse(
            data={"images": data, "folder_path": folder_path},
            message="Successfully retrieved all image objects",
            success=True
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e),
                ),
            },
        )


@router.get("/class-ids",response_model=ClassIDsResponse)
def get_class_ids(path: str = Query(...)):
    try:
        if not path:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content" : ErrorResponse(
                        success=False,
                        error="Missing 'path' parameter",
                        message="Image path is required",
                    ),
                },
            )

        class_ids = get_objects_db(path)
        return ClassIDsResponse(
            success=True,
            message="Successfully retrieved class IDs" if class_ids else "No class IDs found for the image",
            data=class_ids if class_ids else "None"   
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content":ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e)
                ),
            },
        )



@router.post("/add-folder",response_model=AddFolderResponse)
async def add_folder(payload: AddFolderRequest):
    try:
        
        folder_path = payload.folder_path
        if not os.path.isdir(folder_path):
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "content" : ErrorResponse(
                        success=False,
                        error="Invalid folder path",
                        message="The provided path is not a valid directory",
                    )
                },
            )

        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        tasks = []

        for root, _, files in os.walk(folder_path):
            if "PictoPy.thumbnails" in root:
                continue
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
            return AddFolderResponse(
                data=0,
                message="No valid images found in the specified folder",
                success=True
             )

        await asyncio.create_task(process_images(tasks))

        return AddFolderResponse(
            data=len(tasks),
            message=f"Processing {len(tasks)} images from the folder in the background",
            success=True
        )

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content" : ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e)
                )
            },
        )


# generate 400px width or height thumbnails for all the images present the given folder using pillow library
@router.post("/generate-thumbnails",response_model=GenerateThumbnailsResponse)
@exception_handler_wrapper
def generate_thumbnails(payload: GenerateThumbnailsRequest):
    
    folder_paths = payload.folder_paths
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]
    failed_paths = []

    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            failed_paths.append(
                FailedPathResponse(
                    folder_path=folder_path,
                    error="Invalid folder path",
                    message="The provided path is not a valid directory"
                )
            )
            continue

        for root, _, files in os.walk(folder_path):
            # Do not generate thumbnails for the "PictoPy.thumbnails" folder
            if "PictoPy.thumbnails" in root:
                continue

            # Create the "PictoPy.thumbnails" folder in the current directory (`root`)
            thumbnail_folder = os.path.join(root, "PictoPy.thumbnails")
            os.makedirs(thumbnail_folder, exist_ok=True)

            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension in image_extensions:
                    try:
                        # Create a unique thumbnail name based on the file name
                        thumbnail_name = file
                        thumbnail_path = os.path.join(thumbnail_folder, thumbnail_name)

                        # Skip if the thumbnail already exists
                        if os.path.exists(thumbnail_path):
                            continue

                        # Generate the thumbnail
                        img = Image.open(file_path)
                        img.thumbnail((400, 400))
                        img.save(thumbnail_path)
                    except Exception as e:
                        failed_paths.append(
                            FailedPathResponse(
                                folder_path=folder_path,
                                file=file_path,
                                error="Thumbnail generation error",
                                message=f"Error processing file {file}: {str(e)}"
                            )
                        )

    if failed_paths:
        return GenerateThumbnailsResponse(
            success=False,
            message="Some folders or files could not be processed",
            failed_paths=failed_paths
         )

    return GenerateThumbnailsResponse(
       success=True,
       message="Thumbnails generated successfully for all valid folders"
    )


# Delete all the thumbnails present in the given folder
@router.delete("/delete-thumbnails")
@exception_handler_wrapper
def delete_thumbnails(payload: dict):
    if "folder_path" not in payload:
        return JSONResponse(
            status_code=400,
            content={
                "status_code": 400,
                "content": {
                    "success": False,
                    "error": "Missing 'folder_path' in payload",
                    "message": "Folder path is required",
                },
            },
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
                    "message": "The provided path is not a valid directory",
                },
            },
        )

    # List to store any errors encountered while deleting thumbnails
    failed_deletions = []

    # Walk through the folder path and find all `PictoPy.thumbnails` folders
    for root, dirs, _ in os.walk(folder_path):
        for dir_name in dirs:
            if dir_name == "PictoPy.thumbnails":
                thumbnail_folder = os.path.join(root, dir_name)
                try:
                    # Delete the thumbnail folder
                    shutil.rmtree(thumbnail_folder)
                    print(f"Deleted: {thumbnail_folder}")
                except Exception as e:
                    failed_deletions.append(
                        {
                            "folder": thumbnail_folder,
                            "error": str(e),
                        }
                    )

    if failed_deletions:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Some thumbnail folders could not be deleted",
                    "message": "See the `failed_deletions` field for details.",
                    "failed_deletions": failed_deletions,
                },
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "content": {
                "success": True,
                "message": "All PictoPy.thumbnails folders have been successfully deleted.",
            },
        },
    )