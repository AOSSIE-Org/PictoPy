import sqlite3
import os
import json

from app.config.settings import ALBUM_DATABASE_PATH
from app.utils.wrappers import image_exists, album_exists
from app.database.images import is_image_in_database


"""
TODO: Handle case when image is not in database for adding multiple photos to an album? (necessary?)
"""
def create_albums_table():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT PRIMARY KEY,
            image_paths TEXT,
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

    cursor.execute("INSERT INTO albums (album_name, image_paths, description) VALUES (?, ?, ?)",
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

    cursor.execute("SELECT image_paths FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_paths = json.loads(result[0])
    abs_path = os.path.abspath(image_path)
    if abs_path not in image_paths:
        image_paths.append(abs_path)
        cursor.execute("UPDATE albums SET image_paths = ? WHERE album_name = ?",
                       (json.dumps(image_paths), album_name))
        conn.commit()
    conn.close()

@album_exists
def add_photos_to_album(album_name, image_paths):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    # get the current list of image paths for the album
    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        existing_paths = json.loads(result[0])
        # convert image paths to absolute paths and append them to the existing list
        abs_paths = [os.path.abspath(path) for path in image_paths]
        updated_paths = existing_paths + abs_paths

        cursor.execute("""
            UPDATE albums SET image_paths = ? WHERE album_name = ?
        """, (json.dumps(updated_paths), album_name))

    conn.commit()
    conn.close()

@album_exists
def get_album_photos(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT image_paths FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    conn.close()

    return json.loads(result[0]) if result else None

@album_exists
@image_exists
def remove_photo_from_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT image_paths FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_paths = json.loads(result[0])
    abs_path = os.path.abspath(image_path)
    if abs_path in image_paths:
        image_paths.remove(abs_path)
        cursor.execute("UPDATE albums SET image_paths = ? WHERE album_name = ?",
                       (json.dumps(image_paths), album_name))
        conn.commit()
    conn.close()

def get_all_albums():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT album_name, image_paths FROM albums")
    results = cursor.fetchall()
    albums = [{"album_name": name, "image_paths": json.loads(paths)} for name, paths in results]

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