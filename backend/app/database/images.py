# Standard library imports
import sqlite3
import os
import json

# App-specific imports
from app.config.settings import (
    DATABASE_PATH,
)
from app.facecluster.init_face_cluster import get_face_cluster
from app.database.albums import remove_image_from_all_albums


def create_image_id_mapping_table():
    conn = sqlite3.connect(DATABASE_PATH)
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
    conn.close()


def create_images_table():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    create_image_id_mapping_table()  # Ensure dependency table exists

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
    conn.close()


def insert_image_db(path, class_ids, metadata, folder_id=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    class_ids_json = json.dumps(class_ids)
    metadata_json = json.dumps(metadata)

    # Insert mapping if it doesn't already exist

    cursor.execute(
        "INSERT OR IGNORE INTO image_id_mapping (path, folder_id) VALUES (?, ?)",
        (abs_path, folder_id),
    )
    cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
    image_id = cursor.fetchone()[0]

    # Insert or update the image data in the 'images' table

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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)

    try:
        # Get image ID from path
        cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
        result = cursor.fetchone()
        
        if result:
            image_id = result[0]
            # Remove from both tables
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            cursor.execute("DELETE FROM image_id_mapping WHERE id = ?", (image_id,))

            # Remove image from albums (handled separately to avoid circular imports)
            remove_image_from_all_albums(image_id)
            
            # Import only after removing image from albums to avoid circular import error
            from app.database.faces import delete_face_embeddings

            conn.commit()
            
            # Remove image from face clusters
            clusters = get_face_cluster()
            clusters.remove_image(image_id)

            # Delete associated face embeddings
            delete_face_embeddings(image_id)
    finally:
        # Always close the connection, regardless of success or failure
        conn.close()


def get_all_image_ids_from_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM image_id_mapping")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


def get_path_from_id(image_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM image_id_mapping WHERE id = ?", (image_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_id_from_path(path):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    cursor.execute("SELECT id FROM image_id_mapping WHERE path = ?", (abs_path,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_objects_db(path):
    image_id = get_id_from_path(path)

    if image_id is None:
        return None

    # Get class_ids from images table
    conn_images = sqlite3.connect(DATABASE_PATH)
    cursor_images = conn_images.cursor()
    
    try:
        cursor_images.execute("SELECT class_ids FROM images WHERE id = ?", (image_id,))
        result = cursor_images.fetchone()
        
        if not result:
            return None

        class_ids_json = result[0]
        class_ids = json.loads(class_ids_json)
        if isinstance(class_ids, list):
            class_ids = [str(class_id) for class_id in class_ids]
        else:
            class_ids = class_ids.split(",")
    finally:
        conn_images.close()

    # Get class names from mappings table
    conn_mappings = sqlite3.connect(DATABASE_PATH)
    cursor_mappings = conn_mappings.cursor()
    
    try:
        class_names = []
        for class_id in class_ids:
            cursor_mappings.execute(
                "SELECT name FROM mappings WHERE class_id = ?", (class_id,)
            )
            name_result = cursor_mappings.fetchone()
            if name_result:
                class_names.append(name_result[0])
    finally:
        conn_mappings.close()
    
    class_names = list(set(class_names))
    return class_names


def is_image_in_database(path):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    cursor.execute("SELECT COUNT(*) FROM image_id_mapping WHERE path = ?", (abs_path,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def get_all_image_paths():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM image_id_mapping")
        paths = [row[0] for row in cursor.fetchall()]
        return paths if paths else []


def get_all_images_from_folder_id(folder_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT path FROM image_id_mapping WHERE folder_id = ?", (folder_id,)
        )
        image_paths = cursor.fetchall()
        return [row[0] for row in image_paths] if image_paths else []
    finally:
        conn.close()
