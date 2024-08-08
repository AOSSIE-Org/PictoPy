import sqlite3
import os
import json

from app.config.settings import (
    IMAGES_PATH,
    IMAGES_DATABASE_PATH,
    MAPPINGS_DATABASE_PATH,
)
from app.facecluster.init_face_cluster import get_face_cluster
from app.facenet.facenet import detect_faces
from app.utils.classification import get_classes
from app.utils.metadata import extract_metadata
from app.database.albums import remove_image_from_all_albums


def create_image_id_mapping_table():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS image_id_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE
        )
    """
    )
    conn.commit()
    conn.close()


def create_images_table():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()

    create_image_id_mapping_table()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            class_ids TEXT,
            metadata TEXT,
            FOREIGN KEY (id) REFERENCES image_id_mapping(id)
        )
    """
    )

    # cursor.execute("SELECT path FROM image_id_mapping")
    # db_paths = [row[0] for row in cursor.fetchall()]

    # for filename in os.listdir(IMAGES_PATH):
    #     file_path = os.path.abspath(os.path.join(IMAGES_PATH, filename))
    #     if file_path not in db_paths:
    #         print(f"Not in database: {file_path}")
    #         class_ids = get_classes(file_path)
    #         metadata = extract_metadata(file_path)
    #         insert_image_db(file_path, class_ids, metadata)
    #         detect_faces(file_path)
    #     else:
    #         print(f"Already in database: {file_path}")
    conn.commit()
    conn.close()


def insert_image_db(path, class_ids, metadata):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    class_ids_json = json.dumps(class_ids)
    metadata_json = json.dumps(metadata)

    cursor.execute(
        "INSERT OR IGNORE INTO image_id_mapping (path) VALUES (?)", (abs_path,)
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
    conn.close()


def delete_image_db(path):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)

    cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
    result = cursor.fetchone()
    if result:
        image_id = result[0]
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        cursor.execute("DELETE FROM image_id_mapping WHERE id = ?", (image_id,))

        # Instead of calling delete_face_embeddings directly, for circular import error
        remove_image_from_all_albums(image_id)
        from app.database.faces import delete_face_embeddings

        clusters = get_face_cluster()
        clusters.remove_image(image_id)
        delete_face_embeddings(image_id)

    conn.commit()
    conn.close()


def get_all_image_ids_from_db():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM image_id_mapping")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


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


def get_objects_db(path):
    conn_images = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor_images = conn_images.cursor()
    image_id = get_id_from_path(path)

    if image_id is None:
        return None

    cursor_images.execute("SELECT class_ids FROM images WHERE id = ?", (image_id,))
    result = cursor_images.fetchone()
    conn_images.close()

    if not result:
        return None

    class_ids_json = result[0]
    class_ids = json.loads(class_ids_json)
    class_ids = class_ids.split(",")

    conn_mappings = sqlite3.connect(MAPPINGS_DATABASE_PATH)
    cursor_mappings = conn_mappings.cursor()
    class_names = []
    for class_id in class_ids:
        cursor_mappings.execute(
            "SELECT name FROM mappings WHERE class_id = ?", (class_id,)
        )
        name_result = cursor_mappings.fetchone()
        if name_result:
            class_names.append(name_result[0])

    conn_mappings.close()
    class_names = list(set(class_names))
    return class_names


def is_image_in_database(path):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    cursor.execute("SELECT COUNT(*) FROM image_id_mapping WHERE path = ?", (abs_path,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0
