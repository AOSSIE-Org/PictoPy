import sqlite3
import json
import bcrypt
from app.config.settings import ALBUM_DATABASE_PATH
from app.utils.wrappers import image_exists, album_exists
from app.utils.path_id_mapping import get_id_from_path, get_path_from_id
from app.utils.APIError import APIError
from fastapi import status


def create_albums_table():
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM albums WHERE album_name = ?", (album_name,))
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        raise APIError(f"Album '{album_name}' already exists", 409)

    password_hash = None
    if is_hidden and password:
        # Hash the password with bcrypt
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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM albums WHERE album_name = ?", (album_name,))
    conn.commit()
    conn.close()


@album_exists
def add_photo_to_album(album_name, image_path):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    # print("GOT IMAGE ID", image_id, flush=True)
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
    verify_album_access(album_name, password)

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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
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
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE albums SET description = ? WHERE album_name = ?",
        (new_description, album_name),
    )
    conn.commit()
    conn.close()


def remove_image_from_all_albums(image_id):
    conn = sqlite3.connect(ALBUM_DATABASE_PATH)
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
