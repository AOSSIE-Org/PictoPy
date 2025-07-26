import sqlite3
import json
import numpy as np
from app.config.settings import DATABASE_PATH


def create_faces_table():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id INTEGER,
            embeddings TEXT,
            FOREIGN KEY (image_id) REFERENCES image_id_mapping(id) ON DELETE CASCADE
        )
    """
    )
    conn.commit()
    conn.close()
# Creates the 'faces' table to store face embeddings linked to images by image_id.
# The embeddings are stored as JSON text. Enforces foreign key constraint with image_id_mapping.


def insert_face_embeddings(image_path, embeddings):
    from app.database.images import get_id_from_path

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        raise ValueError(f"Image '{image_path}' not found in the database")

    embeddings_json = json.dumps([emb.tolist() for emb in embeddings])

    cursor.execute(
        """
        INSERT OR REPLACE INTO faces (image_id, embeddings)
        VALUES (?, ?)
    """,
        (image_id, embeddings_json),
    )

    conn.commit()
    conn.close()
# Inserts or replaces face embeddings for a given image identified by its path.
# Converts numpy embeddings to JSON for storage.


def get_face_embeddings(image_path):
    from app.database.images import get_id_from_path

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    image_id = get_id_from_path(image_path)
    if image_id is None:
        conn.close()
        return None

    cursor.execute(
        """
        SELECT embeddings FROM faces
        WHERE image_id = ?
    """,
        (image_id,),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        embeddings_json = result[0]
        embeddings = np.array(json.loads(embeddings_json))
        return embeddings
    else:
        return None
# Retrieves and returns the face embeddings as a numpy array for a given image path.
# Returns None if no embeddings are found or image is missing.


def get_all_face_embeddings():
    from app.database.images import get_path_from_id

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT image_id, embeddings FROM faces
    """
    )

    results = cursor.fetchall()
    all_embeddings = []
    for image_id, embeddings_json in results:
        image_path = get_path_from_id(image_id)
        embeddings = np.array(json.loads(embeddings_json))
        all_embeddings.append({"image_path": image_path, "embeddings": embeddings})
    print("returning")
    conn.close()
    return all_embeddings
# Retrieves all face embeddings from the database.
# Returns a list of dictionaries each containing the image path and its associated embeddings.


def delete_face_embeddings(image_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))

    conn.commit()
    conn.close()
# Deletes face embeddings from the database for a specific image ID.


def cleanup_face_embeddings():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT image_id FROM faces")
    face_image_ids = set(row[0] for row in cursor.fetchall())

    cursor.execute("SELECT id FROM image_id_mapping")
    valid_image_ids = set(row[0] for row in cursor.fetchall())

    orphaned_ids = face_image_ids - valid_image_ids

    for orphaned_id in orphaned_ids:
        cursor.execute("DELETE FROM faces WHERE image_id = ?", (orphaned_id,))

    conn.commit()
    conn.close()
# Cleans up the faces table by removing embeddings linked to image IDs
# that no longer exist in the image_id_mapping table (orphans).
