import sqlite3
import os
import json

from app.config.settings import IMAGES_PATH, IMAGES_DATABASE_PATH, MAPPINGS_DATABASE_PATH
from app.utils.classification import get_classes
from app.utils.metadata import extract_metadata


# refactor this to initailize , and add tqdm?

def create_images_table():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()

    # Create the images table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            path TEXT PRIMARY KEY,
            class_ids TEXT,
            metadata TEXT
        )
    """)
    cursor.execute("""
        SELECT path FROM images
    """)
    db_paths = [row[0] for row in cursor.fetchall()]
    # Go through the images folder and print paths not present in the database
    for filename in os.listdir(IMAGES_PATH):
        file_path = os.path.abspath(os.path.join(IMAGES_PATH, filename))
        if file_path not in db_paths:
            print(f"Not in database: {file_path}")
            class_ids = get_classes(file_path)
            metadata = extract_metadata(file_path)
            insert_image_db(file_path, class_ids, metadata)
        else:
            print(f"Already in database: {file_path}")
    conn.commit()
    conn.close()

def insert_image_db(path, class_ids, metadata):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    abs_path = os.path.abspath(path)
    class_ids_json = json.dumps(class_ids)
    metadata_json = json.dumps(metadata)

    cursor.execute("""
        INSERT OR REPLACE INTO images (path, class_ids, metadata)
        VALUES (?, ?, ?)
    """, (abs_path, class_ids_json, metadata_json))

    conn.commit()
    conn.close()

def delete_image_db(path):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()

    # convert to absolute path
    abs_path = os.path.abspath(path)

    # Delete the entry from the images table based on the path
    cursor.execute("""
        DELETE FROM images WHERE path = ?
    """, (abs_path,))

    conn.commit()
    conn.close()

def get_all_image_paths_from_db():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT path FROM images")
    paths = [row[0] for row in cursor.fetchall()]

    conn.close()
    return paths

def get_objects_db(path):
    conn_images = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor_images = conn_images.cursor()

    abs_path = os.path.abspath(path)

    cursor_images.execute("""
        SELECT class_ids FROM images WHERE path = ?
    """, (abs_path,))

    result = cursor_images.fetchone()
    conn_images.close()

    if not result:
        return None

    class_ids_json = result[0]
    class_ids = json.loads(class_ids_json)
    class_ids = class_ids.split(",")
    print(class_ids, type(class_ids), flush=True)

    conn_mappings = sqlite3.connect(MAPPINGS_DATABASE_PATH)
    cursor_mappings = conn_mappings.cursor()
    class_names = []
    for class_id in class_ids:
        cursor_mappings.execute("""
            SELECT name FROM mappings WHERE class_id = ?
        """, (class_id,))
        name_result = cursor_mappings.fetchone()
        if name_result:
            class_names.append(name_result[0])
        #  else:
        #      print(f"UNKNOWN ID --> {class_id}" , flush=True)
        #      class_names.append(f"Unknown (ID: {class_id})")

    conn_mappings.close()
    class_names = list(set(class_names))
    return class_names

def is_image_in_database(path):
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    
    abs_path = os.path.abspath(path)
    
    cursor.execute("""
        SELECT COUNT(*) FROM images WHERE path = ?
    """, (abs_path,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0
