import sqlite3
import os
import json

from app.config.settings import DATABASE_PATH
from app.facecluster.init_face_cluster import get_face_cluster
from app.database.albums import remove_image_from_all_albums
from app.database.connection_pool import get_connection, return_connection


def create_image_id_mapping_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS image_id_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            folder_id INTEGER,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
    """
    )
    conn.commit()
    return_connection(conn)


def create_images_table():
    conn = get_connection()
    cursor = conn.cursor()

    create_image_id_mapping_table()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            class_ids TEXT,
            metadata TEXT,
            FOREIGN KEY (id) REFERENCES image_id_mapping(id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    return_connection(conn)


def insert_image_db(path, class_ids, metadata, folder_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    class_ids_json = json.dumps(class_ids)
    metadata_json = json.dumps(metadata)

    try:
        cursor.execute(
            "INSERT OR IGNORE INTO image_id_mapping (path, folder_id) VALUES (?, ?)",
            (abs_path, folder_id),
        )
        cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
        image_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT OR REPLACE INTO images (id, class_ids, metadata)
            VALUES (?, ?, ?)
        """,
            (image_id, class_ids_json, metadata_json),
        )

        conn.commit()
        return image_id
    finally:
        return_connection(conn)


def delete_image_db(path):
    conn = get_connection()
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)

    try:
        cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
        result = cursor.fetchone()
        if result:
            image_id = result[0]
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            cursor.execute("DELETE FROM image_id_mapping WHERE id = ?", (image_id,))

            # Instead of calling delete_face_embeddings directly, for circular import error
            remove_image_from_all_albums(image_id)
            from app.database.faces import delete_face_embeddings

            conn.commit()
            clusters = get_face_cluster()
            clusters.remove_image(image_id)
            delete_face_embeddings(image_id)
    finally:
        return_connection(conn)


def get_all_image_ids_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM image_id_mapping")
        ids = [row[0] for row in cursor.fetchall()]
        return ids
    finally:
        return_connection(conn)


def get_path_from_id(image_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT path FROM image_id_mapping WHERE id = ?", (image_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        return_connection(conn)


def get_id_from_path(path):
    conn = get_connection()
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    try:
        cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        return_connection(conn)


def get_objects_db(path):
    conn_images = get_connection()
    cursor_images = conn_images.cursor()
    image_id = get_id_from_path(path)

    if image_id is None:
        return None

    try:
        cursor_images.execute("SELECT class_ids FROM images WHERE id = ?", (image_id,))
        result = cursor_images.fetchone()
    finally:
        return_connection(conn_images)

    if not result:
        return None

    class_ids_json = result[0]
    class_ids = json.loads(class_ids_json)
    if isinstance(class_ids, list):
        class_ids = [str(class_id) for class_id in class_ids]
    else:
        class_ids = class_ids.split(",")

    conn_mappings = get_connection()
    cursor_mappings = conn_mappings.cursor()
    class_names = []
    try:
        for class_id in class_ids:
            cursor_mappings.execute(
                "SELECT name FROM mappings WHERE class_id = ?", (class_id,)
            )
            name_result = cursor_mappings.fetchone()
            if name_result:
                class_names.append(name_result[0])
    finally:
        return_connection(conn_mappings)

    class_names = list(set(class_names))
    return class_names


def is_image_in_database(path):
    conn = get_connection()
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    try:
        cursor.execute("SELECT COUNT(*) FROM image_id_mapping WHERE path = ?", (abs_path,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        return_connection(conn)


def get_all_image_paths():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT path FROM image_id_mapping")
        paths = [row[0] for row in cursor.fetchall()]
        return paths if paths else []
    finally:
        return_connection(conn)


def get_all_images_from_folder_id(folder_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT path FROM image_id_mapping WHERE folder_id = ?", (folder_id,)
        )
        image_paths = cursor.fetchall()
        return [row[0] for row in image_paths] if image_paths else []
    finally:
        return_connection(conn)
