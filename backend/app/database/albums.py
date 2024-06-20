import sqlite3
import os
import json

from app.config.settings import ALBUM_DATABASE_PATH

def create_albums_table():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT PRIMARY KEY,
            image_paths TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_album(album_name):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    # check if the album already exists
    cursor.execute("""
        SELECT COUNT(*) FROM albums WHERE album_name = ?
    """, (album_name,))
    count = cursor.fetchone()[0]

    if count == 0:
        # add a new album with an empty list of image paths
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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    # get the current list of image paths for the album
    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        # covnert to abs path first
        abs_path = os.path.abspath(image_path)
        image_paths.append(abs_path)

        cursor.execute("""
            UPDATE albums SET image_paths = ? WHERE album_name = ?
        """, (json.dumps(image_paths), album_name))

    conn.commit()
    conn.close()

def remove_photo_from_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    # get the current list of image paths for the album
    cursor.execute("""
        SELECT image_paths FROM albums WHERE album_name = ?
    """, (album_name,))

    result = cursor.fetchone()
    if result:
        image_paths = json.loads(result[0])
        # convert the image_path to an absolute path and remove it from the list
        abs_path = os.path.abspath(image_path)
        if abs_path in image_paths:
            image_paths.remove(abs_path)

            # update the album with the new list of image paths
            cursor.execute("""
                UPDATE albums SET image_paths = ? WHERE album_name = ?
            """, (json.dumps(image_paths), album_name))

    conn.commit()
    conn.close()

def get_all_albums():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    # fetch all albums and their image paths
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