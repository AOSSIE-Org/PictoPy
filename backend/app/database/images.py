import sqlite3
import os
import json

from app.config.settings import IMAGES_PATH, IMAGES_DATABASE_PATH
from app.utils.classification import get_classes2
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
    print(db_paths)
    # Go through the images folder and print paths not present in the database
    for filename in os.listdir(IMAGES_PATH):
        file_path = os.path.abspath(os.path.join(IMAGES_PATH, filename))
        if file_path not in db_paths:
            print(f"Not in database: {file_path}")
            class_ids = get_classes2(file_path)
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
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()

    # convert to absolute path
    abs_path = os.path.abspath(path)

    # get the id based on key (path)
    cursor.execute("""
        SELECT class_ids FROM images WHERE path = ?
    """, (abs_path,))

    result = cursor.fetchone()
    conn.close()

    if result:
        class_ids_json = result[0]
        class_ids = json.loads(class_ids_json)
        return class_ids
    else:
        return None
    
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
