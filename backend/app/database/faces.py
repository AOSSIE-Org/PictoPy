import sqlite3
import json
from typing import Any
import numpy as np
from app.config.settings import DATABASE_PATH


def create_faces_table() -> None:
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


def insert_face_embeddings(
    image_path: str, embeddings: list[np.ndarray[Any, Any]]
) -> None:
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


def get_face_embeddings(image_path: str) -> np.ndarray | None:
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


def get_all_face_embeddings() -> list[dict[str, Any]]:
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


def delete_face_embeddings(image_id: str) -> None:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))

    conn.commit()
    conn.close()


def cleanup_face_embeddings() -> None:
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
