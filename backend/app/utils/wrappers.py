import sqlite3
import os
from functools import wraps

from app.config.settings import DATABASE_PATH
from app.utils.APIError import APIError
from fastapi import status
from fastapi.responses import JSONResponse


def album_exists(func):
    """
    Decorator to check if an album exists in the database before executing the function.

    Args:
        func: The function to be wrapped

    Raises:
        APIError with 404 status if album does not exist

    Returns:
        The wrapped function's return value if album exists
    """
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


def image_exists(func):
    """
    Decorator to check if an image exists in the database before executing the function.

    Args:
        func: The function to be wrapped

    Raises:
        APIError with 400 status if image path not provided
        APIError with 404 status if image does not exist in the database

    Returns:
        The wrapped function's return value if image exists
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract image_path from args or kwargs
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


def exception_handler_wrapper(func):
    """
    Decorator to wrap a function and handle any exceptions raised,
    returning a JSONResponse with appropriate status code and error message.

    Args:
        func: The function to be wrapped

    Returns:
        JSONResponse containing error details if an exception occurs,
        otherwise the function's return value.
    """
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
