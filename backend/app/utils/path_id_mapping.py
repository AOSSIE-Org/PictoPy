import sqlite3
import os
from app.config.settings import DATABASE_PATH


def get_path_from_id(image_id):
    """
    Retrieve the file path associated with a given image ID from the database.

    Args:
        image_id: The unique identifier for an image.

    Returns:
        The absolute file path as a string if found; otherwise, None.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM image_id_mapping WHERE id = ?", (image_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_id_from_path(path):
    """
    Retrieve the image ID associated with a given file path from the database.

    Args:
        path: The file path to look up.

    Returns:
        The image ID as an integer if found; otherwise, None.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)  # Normalize path to absolute
    cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
