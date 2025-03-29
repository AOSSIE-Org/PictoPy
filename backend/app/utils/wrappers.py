import sqlite3
import os
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from app.config.settings import DATABASE_PATH
from app.utils.APIError import APIError
from fastapi import status
from fastapi.responses import JSONResponse

F = TypeVar("F", bound=Callable[..., Any])


def album_exists(func: F) -> F:
    @wraps(func)
    def wrapper(album_name: str, *args: Any, **kwargs: Any) -> Any:
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

    return cast(F, wrapper)


def image_exists(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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

    return cast(F, wrapper)


def exception_handler_wrapper(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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

    return cast(F, wrapper)
