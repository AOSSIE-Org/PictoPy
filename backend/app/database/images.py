import sqlite3
import os
from app.config.settings import IMAGES_PATH
from app.utils.classification import get_classes2

def create_images_table():
    conn = sqlite3.connect('app/database/images.db')
    cursor = conn.cursor()

    # Create the images table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            path TEXT PRIMARY KEY,
            array TEXT
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
            print(f"Path not in database: {file_path}")
            result = get_classes2(file_path)
            insert_image_db(file_path, result['ids'])
        else:
            print(file_path)
    conn.commit()
    conn.close()

def insert_image_db(path, array):
    conn = sqlite3.connect('app/database/images.db')
    cursor = conn.cursor()
    # exclude the [ and ] and join everything with ,
    lst_str = ','.join(array[1:-1].split())

    # Convert the relative path to an absolute path before inserting into the database
    abs_path = os.path.abspath(path)

    cursor.execute("""
        INSERT OR REPLACE INTO images (path, array)
        VALUES (?, ?)
    """, (abs_path, lst_str))

    conn.commit()
    conn.close()

def extract_ids_from_array(path):
    conn = sqlite3.connect('app/database/images.db')
    cursor = conn.cursor()

    # Convert the relative path to an absolute path before querying the database
    abs_path = os.path.abspath(path)

    # Retrieve the array string from the images table based on the path
    cursor.execute("""
        SELECT array FROM images WHERE path = ?
    """, (abs_path,))

    result = cursor.fetchone()
    conn.close()
    if result:
        ids = result[0].split(',')
        return [int(id) for id in ids]
    else:
        return None