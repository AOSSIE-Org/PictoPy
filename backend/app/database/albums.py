import sqlite3
import json
import bcrypt
from app.config.settings import DATABASE_PATH
from app.utils.wrappers import image_exists, album_exists
from app.utils.path_id_mapping import get_id_from_path, get_path_from_id
from app.utils.APIError import APIError
from fastapi import status


def create_albums_table():
    # Creates the 'albums' table in the database if it doesn't exist.
    # The table stores album name, associated image IDs, description, visibility, and optional password.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT PRIMARY KEY,
            image_ids TEXT,
            description TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_hidden BOOLEAN DEFAULT FALSE,
            password_hash TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def create_album(album_name, description=None, is_hidden=False, password=None):
    # Creates a new album with the given name and optional description and visibility settings.
    # If the album is hidden, a password hash is stored for access control.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM albums WHERE album_name = ?", (album_name,))
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        raise APIError(f"Album '{album_name}' already exists", 409)

    password_hash = None
    if is_hidden and password:
        # Hash the password using bcrypt for secure storage
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    cursor.execute(
        """INSERT INTO albums
        (album_name, image_ids, description, is_hidden, password_hash) 
        VALUES (?, ?, ?, ?, ?)""",
        (album_name, json.dumps([]), description, is_hidden, password_hash),
    )
    conn.commit()
    conn.close()


def verify_album_access(album_name, password=None):
    # Verifies if access to a hidden album is authorized.
    # Raises an error if album doesn't exist or if password is required and incorrect.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """SELECT is_hidden, password_hash FROM albums WHERE album_name = ?""",
        (album_name,),
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise APIError(f"Album '{album_name}' not found", status.HTTP_404_NOT_FOUND)

    is_hidden, password_hash = result

    if is_hidden:
        if not password:
            raise APIError(
                "Password required for hidden album", status.HTTP_401_UNAUTHORIZED
            )

        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            raise APIError("Invalid password", status.HTTP_401_UNAUTHORIZED)

    return True


@album_exists
def delete_album(album_name):
    # Deletes an album and all its associated image references from the database.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM albums WHERE album_name = ?", (album_name,))
    conn.commit()
    conn.close()


@album_exists
def add_photo_to_album(album_name, image_path):
    # Adds an image to an album by converting the image path to its ID and updating the album's image list.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        raise APIError(
            f"Image '{image_path}' not found in the database", status.HTTP_404_NOT_FOUND
        )

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_ids = json.loads(result[0])
    if image_id not in image_ids:
        image_ids.append(image_id)
        cursor.execute(
            "UPDATE albums SET image_ids = ? WHERE album_name = ?",
            (json.dumps(image_ids), album_name),
        )
        conn.commit()
    conn.close()


@album_exists
def get_album_photos(album_name, password=None):
    # Retrieves the list of image paths in the album after verifying access (if hidden).
    verify_album_access(album_name, password)

    conn = sqlite3.connect(DATABASE_PATH)
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
    # Removes an image from a specific album, if the image exists in it.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        raise APIError(
            f"Image '{image_path}' not found in the database", status.HTTP_404_NOT_FOUND
        )

    cursor.execute("SELECT image_ids FROM albums WHERE album_name = ?", (album_name,))
    result = cursor.fetchone()
    image_ids = json.loads(result[0])
    if image_id in image_ids:
        image_ids.remove(image_id)
        cursor.execute(
            "UPDATE albums SET image_ids = ? WHERE album_name = ?",
            (json.dumps(image_ids), album_name),
        )
        conn.commit()
    conn.close()


def get_all_albums(include_hidden=False):
    # Retrieves metadata for all albums.
    # If `include_hidden` is False, only visible (non-hidden) albums are returned.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if include_hidden:
        cursor.execute(
            "SELECT album_name, image_ids, description, is_hidden FROM albums"
        )
    else:
        cursor.execute(
            """SELECT album_name, image_ids, description, is_hidden 
            FROM albums WHERE is_hidden = FALSE"""
        )

    results = cursor.fetchall()
    albums = [
        {
            "album_name": name,
            "image_paths": [get_path_from_id(id) for id in json.loads(ids)],
            "description": description,
            "is_hidden": hidden,
        }
        for name, ids, description, hidden in results
    ]

    conn.close()
    return albums


@album_exists
def edit_album_description(album_name, new_description):
    # Updates the description of a specific album.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE albums SET description = ? WHERE album_name = ?",
        (new_description, album_name),
    )
    conn.commit()
    conn.close()


def remove_image_from_all_albums(image_id):
    # Removes an image ID from all albums in which it appears.
    # Useful when an image is deleted from the system.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT album_name, image_ids FROM albums")
    albums = cursor.fetchall()

    for album_name, image_ids_json in albums:
        image_ids = json.loads(image_ids_json)
        if image_id in image_ids:
            image_ids.remove(image_id)
            cursor.execute(
                "UPDATE albums SET image_ids = ? WHERE album_name = ?",
                (json.dumps(image_ids), album_name),
            )

    conn.commit()
    conn.close()
