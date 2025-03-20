import sqlite3
import json
import numpy as np
from app.config.settings import DATABASE_PATH
from app.database.connection_pool import get_connection, return_connection


def create_faces_table():
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
    finally:
        return_connection(conn)


def insert_face_embeddings(image_path, embeddings):
    from app.database.images import get_id_from_path

    conn = get_connection()
    cursor = conn.cursor()

    try:
        image_id = get_id_from_path(image_path)
        if image_id is None:
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
    finally:
        return_connection(conn)


def get_face_embeddings(image_path):
    from app.database.images import get_id_from_path

    image_id = get_id_from_path(image_path)
    if image_id is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT embeddings FROM faces
            WHERE image_id = ?
        """,
            (image_id,),
        )

        result = cursor.fetchone()
        
        if result:
            embeddings_json = result[0]
            embeddings = np.array(json.loads(embeddings_json))
            return embeddings
        else:
            return None
    finally:
        return_connection(conn)


def get_all_face_embeddings():
    from app.database.images import get_path_from_id

    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        return all_embeddings
    finally:
        return_connection(conn)


def delete_face_embeddings(image_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))
        conn.commit()
    finally:
        return_connection(conn)


def cleanup_face_embeddings():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT image_id FROM faces")
        face_image_ids = set(row[0] for row in cursor.fetchall())

        cursor.execute("SELECT id FROM image_id_mapping")
        valid_image_ids = set(row[0] for row in cursor.fetchall())

        orphaned_ids = face_image_ids - valid_image_ids

        for orphaned_id in orphaned_ids:
            cursor.execute("DELETE FROM faces WHERE image_id = ?", (orphaned_id,))

        conn.commit()
    finally:
        return_connection(conn)
