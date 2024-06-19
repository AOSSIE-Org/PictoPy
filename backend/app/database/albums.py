import sqlite3
import os
import json

from app.config.settings import ALBUMS_DATABASE_PATH

def create_albums_table():
    conn = sqlite3.connect(ALBUMS_DATABASE_PATH)
    cursor = conn.cursor()

    # create the albums table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT PRIMARY KEY,
            image_paths TEXT
        )
    """)

    conn.commit()
    conn.close()

def create_album(album_name):
    conn = sqlite3.connect(ALBUMS_DATABASE_PATH)
    cursor = conn.cursor()

    # Insert a new album with an empty list of image paths
    cursor.execute("""
        INSERT OR REPLACE INTO albums (album_name, image_paths)
        VALUES (?, ?)
    """, (album_name, json.dumps([])))

    conn.commit()
    conn.close()

def delete_album(album_name):
    conn = sqlite3.connect(ALBUMS_DATABASE_PATH)
    cursor = conn.cursor()

    # Delete the album based on the album_name
    cursor.execute("""
        DELETE FROM albums WHERE album_name = ?
    """, (album_name,))

    conn.commit()
    conn.close()

def add_photo_to_album(album_name, image_path):
    conn = sqlite3.connect(ALBUMS_DATABASE_PATH)
    cursor = conn.cursor()

    # Get the current list of image paths for the album
    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        # Convert image_path to absolute path and append it to the list
        abs_path = os.path.abspath(image_path)
        image_paths.append(abs_path)

        # Update the album with the new list of image paths
        cursor.execute("""
            UPDATE albums SET image_paths = ? WHERE album_name = ?
        """, (json.dumps(image_paths), album_name))

    conn.commit()
    conn.close()

def remove_photo_from_album(album_name, image_path):
    conn = sqlite3.connect(ALBUMS_DATABASE_PATH)
    cursor = conn.cursor()

    # Get the current list of image paths for the album
    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        # Convert image_path to absolute path and remove it from the list
        abs_path = os.path.abspath(image_path)
        if abs_path in image_paths:
            image_paths.remove(abs_path)

            # Update the album with the new list of image paths
            cursor.execute("""
                UPDATE albums SET image_paths = ? WHERE album_name = ?
            """, (json.dumps(image_paths), album_name))

    conn.commit()
    conn.close()