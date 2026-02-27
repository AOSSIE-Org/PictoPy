import os
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import db_get_all_images, db_get_image_path_by_id
from app.schemas.images import ErrorResponse, RenameImageRequest, RenameImageResponse
from app.utils.images import image_util_parse_metadata
from pydantic import BaseModel
from app.database.images import db_toggle_image_favourite_status
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class MetadataModel(BaseModel):
    name: str
    date_created: Optional[str]
    width: int
    height: int
    file_location: str
    file_size: int
    item_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


class ImageData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


@router.get(
    "/",
    response_model=GetAllImagesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_images(
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status")
):
    """Get all images from the database."""
    try:
        # Get all images with tags from database (single query with optional filter)
        images = db_get_all_images(tagged=tagged)

        # Convert to response format
        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image_util_parse_metadata(image["metadata"]),
                isTagged=image["isTagged"],
                isFavourite=image.get("isFavourite", False),
                tags=image["tags"],
            )
            for image in images
        ]

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} images",
            data=image_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images: {str(e)}",
            ).model_dump(),
        )


# adding add to favourite and remove from favourite routes


class ToggleFavouriteRequest(BaseModel):
    image_id: str


@router.post("/toggle-favourite")
def toggle_favourite(req: ToggleFavouriteRequest):
    image_id = req.image_id
    try:
        success = db_toggle_image_favourite_status(image_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Image not found or failed to toggle"
            )
        # Fetch updated status to return
        image = next(
            (img for img in db_get_all_images() if img["id"] == image_id), None
        )
        return {
            "success": True,
            "image_id": image_id,
            "isFavourite": image.get("isFavourite", False),
        }

    except Exception as e:
        logger.error(f"error in /toggle-favourite route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


class ImageInfoResponse(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None


@router.put(
    "/rename-image",
    response_model=RenameImageResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def rename_image(request: RenameImageRequest):
    """
    Rename an image file on disk based on its image ID.

    The database record is updated separately by the sync microservice.
    """
    try:
        image_id = request.image_id.strip()
        raw_name = request.rename
        new_name = raw_name.strip()

        if not image_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="Image ID cannot be empty",
                ).model_dump(),
            )

        if not new_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="New image name cannot be empty",
                ).model_dump(),
            )

        # Disallow filesystem separators and common invalid characters (especially on Windows),
        # plus a few extra characters that are prone to shell/filesystem issues.
        invalid_chars = set('<>:"/\\\\|?*!^')
        if any(ch in invalid_chars for ch in new_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="New image name contains invalid characters.",
                ).model_dump(),
            )

        # Additional Windows-safe validations
        # Reject names that are '.' or '..' or that consist only of dots
        if all(ch == "." for ch in new_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="New image name cannot be '.' , '..' or consist only of dots.",
                ).model_dump(),
            )

        # Reject names that end with a dot or a space (Windows trims these)
        if raw_name and (raw_name.endswith(".") or raw_name.endswith(" ")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="New image name cannot end with a dot or space.",
                ).model_dump(),
            )

        # Reject names whose base stem matches Windows reserved device names
        reserved_device_names = {
            "CON",
            "PRN",
            "NUL",
            "AUX",
            *[f"COM{i}" for i in range(1, 10)],
            *[f"LPT{i}" for i in range(1, 10)],
        }
        base_stem = new_name.split(".", 1)[0]
        if base_stem and base_stem.upper() in reserved_device_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message=(
                        "New image name cannot use a reserved Windows device name "
                        "(CON, PRN, NUL, AUX, COM1–COM9, LPT1–LPT9)."
                    ),
                ).model_dump(),
            )

        image_path = db_get_image_path_by_id(image_id)
        if not image_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Image Not Found",
                    message=f"Image with ID '{image_id}' does not exist.",
                ).model_dump(),
            )

        folder_path = os.path.dirname(image_path)
        extension = os.path.splitext(image_path)[1]
        new_file_path = os.path.join(folder_path, new_name + extension)

        # Atomically reserve the target path to avoid TOCTOU between existence
        # checks and rename operations.
        placeholder_created = False
        try:
            try:
                fd = os.open(
                    new_file_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.close(fd)
                placeholder_created = True
            except FileExistsError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        success=False,
                        error="File Exists",
                        message="A file with the new name already exists.",
                    ).model_dump(),
                )

            # Perform the actual rename now that the name is reserved.
            os.rename(image_path, new_file_path)
        except HTTPException:
            # Bubble up HTTP errors (e.g., file already exists).
            raise
        except Exception as e:
            # Clean up the placeholder if the rename failed unexpectedly.
            if placeholder_created:
                try:
                    os.unlink(new_file_path)
                except OSError as cleanup_err:
                    logger.error(
                        f"Failed to clean up placeholder file '{new_file_path}': {cleanup_err}"
                    )
            # Re-raise for the outer exception handler to translate.
            raise e

        return RenameImageResponse(
            success=True,
            message=f"Successfully renamed image to '{new_name}{extension}'",
        )

    except HTTPException as e:
        # Re-raise HTTPExceptions to preserve their status codes and details.
        raise e
    except Exception as e:
        logger.error(f"Error renaming image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to rename image: {str(e)}",
            ).model_dump(),
        )
