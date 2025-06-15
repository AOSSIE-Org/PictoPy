import os
import asyncio
from fastapi import APIRouter, Query, HTTPException
from fastapi import status as fastapi_status
from fastapi.responses import JSONResponse

from app.config.settings import IMAGES_PATH

from app.facenet.facenet import detect_faces
from app.utils.classification import get_classes
from app.utils.wrappers import exception_handler_wrapper
from app.utils.generateThumbnails import (
    generate_thumbnails_for_folders,
    generate_thumbnails_for_existing_folders,
)
from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.database.images import (
    get_all_image_ids_from_db,
    get_path_from_id,
    insert_image_db,
    delete_image_db,
    get_objects_db,
    get_all_image_paths,
    get_all_images_from_folder_id,
)
from app.utils.metadata import extract_metadata
from app.database.folders import (
    insert_folder,
    get_folder_id_from_path,
    delete_folder,
)

from app.schemas.images import (
    DeleteImageRequest,
    DeleteImageResponse,
    DeleteMultipleImagesRequest,
    DeleteMultipleImagesResponse,
    GetAllImageObjectsResponse,
    ErrorResponse,
    ImagesResponse,
    AddFolderRequest,
    AddFolderResponse,
    GenerateThumbnailsRequest,
    GenerateThumbnailsResponse,
    ClassIDsResponse,
    GetImagesResponse,
    DeleteThumbnailsRequest,
    DeleteThumbnailsResponse,
    FailedDeletionThumbnailResponse,
)

router = APIRouter()

progress_status = {}


async def run_get_classes(img_path, folder_id=None):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path), folder_id)
    if result:
        classes = result.split(",")
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)


@router.get(
    "/all-images",
    response_model=GetImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_images():
    try:
        image_files = get_all_image_paths()

        print("Image Files = ", image_files)

        return GetImagesResponse(
            data=ImagesResponse(
                image_files=image_files, folder_path=os.path.abspath(IMAGES_PATH)
            ),
            message="Successfully retrieved all images",
            success=True,
        )

    except Exception:
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Failed to get all images",
            ).model_dump(),
        )


async def process_images(tasks, folder_id):
    total = len(tasks)
    completed = 0
    progress_status[folder_id] = {"total": total, "completed": 0, "status": "pending"}

    for coro in asyncio.as_completed(tasks):
        await coro
        completed += 1
        progress_status[folder_id]["completed"] = completed
        await asyncio.sleep(0)

    progress_status[folder_id]["status"] = "completed"


@router.delete(
    "/delete-image",
    response_model=DeleteImageResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def delete_image(payload: DeleteImageRequest):
    try:
        filename = payload.path
        file_path = os.path.join(IMAGES_PATH, filename)

        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Image not found",
                    message="Image file not found",
                ).model_dump(),
            )

        os.remove(file_path)
        delete_image_db(file_path)
        return DeleteImageResponse(
            data=file_path, message="Image deleted successfully", success=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal server error", message=str(e)
            ).model_dump(),
        )


@router.delete(
    "/multiple-images",
    response_model=DeleteMultipleImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def delete_multiple_images(payload: DeleteMultipleImagesRequest):
    try:
        paths = payload.paths
        is_from_device = payload.isFromDevice
        deleted_paths = []
        folder_paths = set()

        for path in paths:
            if not os.path.isfile(path):
                raise HTTPException(
                    status_code=fastapi_status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        success=False,
                        error="Image not found",
                        message=f"Image file not found : {path}",
                    ).model_dump(),
                )

            path = os.path.normpath(path)
            folder_path, filename = os.path.split(path)
            folder_paths.add(folder_path)

            thumbnail_folder = os.path.abspath(
                os.path.join(THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails")
            )
            thumb_nail_image_path = os.path.join(thumbnail_folder, filename)

            print("File = ", filename)

            # Check and remove the original file
            if os.path.exists(path):
                try:
                    if is_from_device:
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
                    print("Successfully removed!")
                except PermissionError:
                    print(f"Permission denied for file '{thumb_nail_image_path}'.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                print(f"File '{thumb_nail_image_path}' does not exist.")

            delete_image_db(path)
            deleted_paths.append(path)

        # Delete those folders , no image left
        for folder_path in folder_paths:
            try:
                folder_id = get_folder_id_from_path(folder_path)
                images = get_all_images_from_folder_id(folder_id)
                if not len(images):
                    delete_folder(folder_path)
            except Exception:
                print("Folder deletion Unsuccessful")

        return DeleteMultipleImagesResponse(
            data=deleted_paths, message="Images deleted successfully", success=True
        )

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Failed to delete images",
            ).model_dump(),
        )


@router.get(
    "/all-image-objects",
    response_model=GetAllImageObjectsResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_all_image_objects():
    try:
        generate_thumbnails_for_existing_folders()
        image_ids = get_all_image_ids_from_db()
        data = {}
        for image_id in image_ids:
            image_path = get_path_from_id(image_id)
            classes = get_objects_db(image_path)
            data[image_path] = classes if classes else "None"
            print(image_path)

        thubnail_image_path = os.path.abspath(
            os.path.join(THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails")
        )

        return GetAllImageObjectsResponse(
            data={"images": data, "image_path": thubnail_image_path},
            message="Successfully retrieved all image objects",
            success=True,
        )

    except Exception:
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Failed to get all images",
            ).model_dump(),
        )


@router.get(
    "/class-ids",
    response_model=ClassIDsResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def get_class_ids(path: str = Query(...)):
    try:
        if not path:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Missing 'path' parameter",
                    message="Image path is required",
                ).model_dump(),
            )

        class_ids = get_objects_db(path)
        return ClassIDsResponse(
            success=True,
            message="Successfully retrieved class IDs"
            if class_ids
            else "No class IDs found for the image",
            data=class_ids if class_ids else "None",
        )

    except Exception:
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Failed to get class IDs",
            ).model_dump(),
        )


@router.post(
    "/add-folder",
    response_model=AddFolderResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 401, 500]},
)
async def add_folder(payload: AddFolderRequest):
    try:
        folder_paths = payload.folder_path

        for folder in folder_paths:
            if not os.path.isdir(folder):
                print("Not OS DIR")
                raise HTTPException(
                    status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        success=False,
                        error="Invalid folder path",
                        message="The provided path is not a valid directory",
                    ).model_dump(),
                )

            if (
                not os.access(folder, os.R_OK)
                or not os.access(folder, os.W_OK)
                or not os.access(folder, os.X_OK)
            ):
                raise HTTPException(
                    status_code=fastapi_status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorResponse(
                        success=False,
                        error="Permission denied",
                        message="The app does not have read and write permissions for the specified folder",
                    ),
                )

            folder_id = get_folder_id_from_path(folder)
            if folder_id is None:
                folder_id = insert_folder(folder)
            if folder_id is None:
                print("Could not insert folder", folder_id)
                return JSONResponse(
                    status_code=400,
                    content={
                        "status_code": 400,
                        "content": {
                            "success": False,
                            "error": "Folder not inserted",
                            "message": "Could not insert folder",
                        },
                    },
                )

            image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
            tasks = []

            for root, _, files in os.walk(folder):
                if "PictoPy.thumbnails" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file_path)[1].lower()
                    if file_extension in image_extensions:
                        tasks.append(
                            asyncio.create_task(
                                run_get_classes(file_path, folder_id=folder_id)
                            )
                        )

            if not tasks:
                return AddFolderResponse(
                    data=0,
                    message="No valid images found in the specified folder",
                    success=True,
                )

            progress_status[folder_id] = {
                "total": len(tasks),
                "completed": 0,
                "status": "pending",
            }
            asyncio.create_task(process_images(tasks, folder_id))

        return AddFolderResponse(
            data=len(tasks),
            message=f"Processing {len(tasks)} images from the folder in the background",
            success=True,
        )

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Failed to add a folder",
            ).model_dump(),
        )


@router.delete("/delete-folder")
@exception_handler_wrapper
def delete_folder_ai_tagging(payload: dict):
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

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                delete_image_db(os.path.join(root, file))

    delete_folder(folder_path)

    return JSONResponse(
        status_code=200,
        content={
            "data": "",
            "message": "Folder deleted successfully",
            "success": True,
        },
    )


@router.post("/generate-thumbnails")
@exception_handler_wrapper
def generate_thumbnails(payload: GenerateThumbnailsRequest):
    folder_paths = payload.folder_paths
    failed_paths = generate_thumbnails_for_folders(folder_paths)
    if failed_paths:
        return GenerateThumbnailsResponse(
            success=False,
            message="Some folders or files could not be processed",
            failed_paths=failed_paths,
        )

    return GenerateThumbnailsResponse(
        success=True, message="Thumbnails generated successfully for all valid folders"
    )


@router.get("/get-thumbnail-path")
@exception_handler_wrapper
def get_thumbnail_path():
    print("GET request Received!")
    thumbnail_path = os.path.abspath(
        os.path.join(THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails")
    )
    print("Thumbnail Path = ", thumbnail_path)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "thumbnailPath": thumbnail_path,
        },
    )


# Delete all the thumbnails present in the given folder
@router.delete(
    "/delete-thumbnails",
    response_model=DeleteThumbnailsResponse,
    responses={
        500: {"model": FailedDeletionThumbnailResponse},
        400: {"model": ErrorResponse},
    },
)
@exception_handler_wrapper
def delete_thumbnails(payload: DeleteThumbnailsRequest):
    folder_path = payload.folder_path

    if not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Invalid folder path",
                message="The provided path is not a valid directory",
            ).model_dump(),
        )

    # List to store any errors encountered while deleting thumbnails
    failed_deletions = []

    for file in os.listdir(folder_path):
        try:
            thumbnail_image_path = os.path.join(
                THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails", file
            )
            if os.path.exists(thumbnail_image_path):
                os.remove(thumbnail_image_path)
        except Exception:
            failed_deletions.append(thumbnail_image_path)

    if failed_deletions:
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FailedDeletionThumbnailResponse(
                success=False,
                message="See the `failed_deletions` field for details.",
                error="Some thumbnail folders could not be deleted",
                failed_deletions=failed_deletions,
            ).model_dump(),
        )

    return DeleteThumbnailsResponse(
        success=True,
        message="All PictoPy.thumbnails folders have been successfully deleted.",
    )


@router.get("/add-folder-progress")
@exception_handler_wrapper
def combined_progress():
    total_tasks = 0
    total_completed = 0
    for status in progress_status.values():
        total_tasks += status["total"]
        total_completed += status["completed"]
    progress = 100 if total_tasks == 0 else int((total_completed / total_tasks) * 100)
    return JSONResponse(
        status_code=200,
        content={
            "data": progress,
            "message": progress_status,
            "success": True,
        },
    )
