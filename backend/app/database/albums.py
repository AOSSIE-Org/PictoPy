import sqlite3
import os
import json

from app.config.settings import ALBUM_DATABASE_PATH, IMAGES_DATABASE_PATH
from app.database.images import is_image_in_database


def create_album(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM albums WHERE album_name = ?
    """, (album_name,))
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        raise ValueError(f"Album '{album_name}' already exists")

    cursor.execute("""
        INSERT INTO albums (album_name, image_paths)
        VALUES (?, ?)
    """, (album_name, json.dumps([])))
    conn.commit()
    conn.close()

def delete_album(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM albums WHERE album_name = ?
    """, (album_name,))

    conn.commit()
    conn.close()

def add_photo_to_album(album_name, image_path):
    if not is_image_in_database(image_path):
        raise ValueError(f"Image '{image_path}' does not exist in the database")

    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        abs_path = os.path.abspath(image_path)
        if abs_path not in image_paths:
            image_paths.append(abs_path)
            cursor.execute("""
                UPDATE albums SET image_paths = ? WHERE album_name = ?
            """, (json.dumps(image_paths), album_name))
            conn.commit()
    else:
        conn.close()
        raise ValueError(f"Album '{album_name}' does not exist")

    conn.close()

def add_photos_to_album(album_name, image_paths):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        existing_paths = json.loads(result[0])
        abs_paths = []
        for path in image_paths:
            if not is_image_in_database(path):
                raise ValueError(f"Image '{path}' does not exist in the database")
            abs_path = os.path.abspath(path)
            if abs_path not in existing_paths:
                abs_paths.append(abs_path)
        
        updated_paths = existing_paths + abs_paths

        cursor.execute("""
            UPDATE albums SET image_paths = ? WHERE album_name = ?
        """, (json.dumps(updated_paths), album_name))
    else:
        conn.close()
        raise ValueError(f"Album '{album_name}' does not exist")

    conn.commit()
    conn.close()

def get_album_photos(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    conn.close()

    if result:
        image_paths = json.loads(result[0])
        return image_paths
    else:
        return None

def remove_photo_from_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        abs_path = os.path.abspath(image_path)
        if abs_path in image_paths:
            image_paths.remove(abs_path)

            cursor.execute("""
                UPDATE albums SET image_paths = ? WHERE album_name = ?
            """, (json.dumps(image_paths), album_name))
    else:
        conn.close()
        raise ValueError(f"Album '{album_name}' does not exist")

    conn.commit()
    conn.close()

def get_all_albums():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT album_name, image_paths FROM albums
    """)

    results = cursor.fetchall()
    albums = []
    for result in results:
        album_name = result[0]
        image_paths = json.loads(result[1])
        albums.append({"album_name": album_name, "image_paths": image_paths})

    conn.close()
    return albums