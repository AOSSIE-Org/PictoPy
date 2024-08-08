import sqlite3
import os
from functools import wraps

from app.config.settings import ALBUM_DATABASE_PATH, IMAGES_DATABASE_PATH


def album_exists(func):
    @wraps(func)
    def wrapper(album_name, *args, **kwargs):
        conn = sqlite3.connect(ALBUM_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM albums WHERE album_name = ?", (album_name,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            raise ValueError(f"Album '{album_name}' does not exist")
        return func(album_name, *args, **kwargs)

    return wrapper


def image_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        image_path = args[1] if len(args) > 1 else kwargs.get("image_path")
        if not image_path:
            raise ValueError("Image path not provided")

        conn = sqlite3.connect(IMAGES_DATABASE_PATH)
        cursor = conn.cursor()
        abs_path = os.path.abspath(image_path)

        cursor.execute(
            "SELECT COUNT(*) FROM image_id_mapping WHERE path = ?", (abs_path,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            raise ValueError(f"Image '{image_path}' does not exist in the database")
        return func(*args, **kwargs)

    return wrapper
