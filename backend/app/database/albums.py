import sqlite3
import json

from app.config.settings import ALBUM_DATABASE_PATH
from app.utils.wrappers import image_exists, album_exists
from app.database.images import get_id_from_path, get_path_from_id

def create_albums_table():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT PRIMARY KEY,
            image_ids TEXT,
            description TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def create_album(album_name, description=None):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM albums WHERE album_name = ?", (album_name,))
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        raise ValueError(f"Album '{album_name}' already exists")

    cursor.execute("INSERT INTO albums (album_name, image_ids, description) VALUES (?, ?, ?)",
                   (album_name, json.dumps([]), description))
    conn.commit()
    conn.close()

@album_exists
def delete_album(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM albums WHERE album_name = ?", (album_name,))
    conn.commit()
    conn.close()

@album_exists
@image_exists
def add_photo_to_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        raise ValueError(f"Image '{image_path}' not found in the database")

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_ids = json.loads(result[0])
    if image_id not in image_ids:
        image_ids.append(image_id)
        cursor.execute("UPDATE albums SET image_ids = ? WHERE album_name = ?",
                       (json.dumps(image_ids), album_name))
        conn.commit()
    conn.close()

@album_exists
def add_photos_to_album(album_name, image_paths):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    if result:
        existing_ids = json.loads(result[0])
        new_ids = [get_id_from_path(path) for path in image_paths if get_id_from_path(path) is not None]
        updated_ids = list(set(existing_ids + new_ids))

        cursor.execute("UPDATE albums SET image_ids = ? WHERE album_name = ?",
                       (json.dumps(updated_ids), album_name))

    conn.commit()
    conn.close()

@album_exists
def get_album_photos(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        image_ids = json.loads(result[0])
        return [get_path_from_id(image_id) for image_id in image_ids]
    return None

@album_exists
@image_exists
def remove_photo_from_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        raise ValueError(f"Image '{image_path}' not found in the database")

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_ids = json.loads(result[0])
    if image_id in image_ids:
        image_ids.remove(image_id)
        cursor.execute("UPDATE albums SET image_ids = ? WHERE album_name = ?",
                       (json.dumps(image_ids), album_name))
        conn.commit()
    conn.close()

def get_all_albums():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT album_name, image_ids FROM albums")
    results = cursor.fetchall()
    albums = [{"album_name": name, "image_paths": [get_path_from_id(id) for id in json.loads(ids)]} for name, ids in results]

    conn.close()
    return albums

@album_exists
def edit_album_description(album_name, new_description):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE albums SET description = ? WHERE album_name = ?",
                   (new_description, album_name))
    conn.commit()
    conn.close()
