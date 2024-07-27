import sqlite3
import os
from app.config.settings import IMAGES_DATABASE_PATH


def get_path_from_id(image_id):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM image_id_mapping WHERE id = ?", (image_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_id_from_path(path):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
