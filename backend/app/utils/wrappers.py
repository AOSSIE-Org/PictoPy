import sqlite3
import os
from functools import wraps

from app.config.settings import DATABASE_PATH
from app.utils.APIError import APIError
from fastapi import status
from fastapi.responses import JSONResponse


def album_exists(func):
    @wraps(func)
    def wrapper(album_name, *args, **kwargs):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM albums WHERE album_name = ?", (album_name,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            raise APIError(
                f"Album '{album_name}' does not exist", status.HTTP_404_NOT_FOUND
            )
        return func(album_name, *args, **kwargs)

    return wrapper


# This decorator checks if an album with the given album_name exists in the database.
# If the album does not exist, it raises an APIError with HTTP 404 status.
# Otherwise, it allows the wrapped function to execute normally.


def image_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        image_path = args[1] if len(args) > 1 else kwargs.get("image_path")
        if not image_path:
            raise APIError("Image path not provided", status.HTTP_400_BAD_REQUEST)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        abs_path = os.path.abspath(image_path)

        cursor.execute(
            "SELECT COUNT(*) FROM image_id_mapping WHERE path = ?", (abs_path,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            raise APIError(
                f"Image '{image_path}' does not exist in the database",
                status.HTTP_404_NOT_FOUND,
            )
        return func(*args, **kwargs)

    return wrapper


# This decorator verifies whether an image exists in the database by checking its absolute file path.
# If the image path is missing or the image is not found in the database,
# it raises an APIError with appropriate HTTP status codes.
# Otherwise, it proceeds to execute the wrapped function.


def exception_handler_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            status_code = hasattr(exc, "status_code") and exc.status_code or 500
            return JSONResponse(
                status_code=status_code,
                content={
                    "statusCode": status_code,
                    "success": False,
                    "error": str(exc),
                },
            )

    return wrapper


# This decorator wraps any function to provide a generic exception handling mechanism.
# If an exception occurs during the function execution,
# it catches the exception and returns a JSONResponse with the error message and status code.
# This helps standardize API error responses.
