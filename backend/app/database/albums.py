import sqlite3
import bcrypt
from app.config.settings import DATABASE_PATH
from app.database.connection import get_db_connection


def db_create_albums_table() -> None:
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS albums (
                album_id TEXT PRIMARY KEY,
                album_name TEXT UNIQUE,
                description TEXT,
                is_hidden BOOLEAN DEFAULT 0,
                password_hash TEXT
            )
            """
        )
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def db_create_album_images_table() -> None:
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS album_images (
                album_id TEXT,
                image_id TEXT,
                PRIMARY KEY (album_id, image_id),
                FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def db_get_all_albums(show_hidden: bool = False):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        if show_hidden:
            cursor.execute("SELECT * FROM albums")
        else:
            cursor.execute("SELECT * FROM albums WHERE is_hidden = 0")
        albums = cursor.fetchall()
        return albums
    finally:
        conn.close()


def db_get_album_by_name(name: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM albums WHERE album_name = ?", (name,))
        album = cursor.fetchone()
        return album if album else None
    finally:
        conn.close()


def db_get_album(album_id: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM albums WHERE album_id = ?", (album_id,))
        album = cursor.fetchone()
        return album if album else None
    finally:
        conn.close()


def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    is_hidden: bool = False,
    password: str = None,
):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        cursor.execute(
            """
            INSERT INTO albums (album_id, album_name, description, is_hidden, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (album_id, album_name, description, int(is_hidden), password_hash),
        )
        conn.commit()
    finally:
        conn.close()


def db_update_album(
    album_id: str,
    album_name: str,
    description: str,
    is_hidden: bool,
    password: str = None,
):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        if password is not None:
            # Update with new password
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_hidden = ?, password_hash = ?
                WHERE album_id = ?
                """,
                (album_name, description, int(is_hidden), password_hash, album_id),
            )
        else:
            # Update without changing password
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_hidden = ?
                WHERE album_id = ?
                """,
                (album_name, description, int(is_hidden), album_id),
            )
        conn.commit()
    finally:
        conn.close()


def db_delete_album(album_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))


def db_get_album_images(album_id: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT image_id FROM album_images WHERE album_id = ?", (album_id,)
        )
        images = cursor.fetchall()
        return [img[0] for img in images]
    finally:
        conn.close()


def db_add_images_to_album(album_id: str, image_ids: list[str]):
    """
    Safely adds images to an album using parameterized queries.
    Maintains UUID support and uses efficient single queries.
    """
    # Validate input type
    if not isinstance(image_ids, list):
        raise ValueError("image_ids must be a list of IDs")

    # Remove integer conversion - keep IDs as strings for UUID support
    sanitized_ids = []
    for img_id in image_ids:
        # Basic validation - ensure it's a non-empty string
        if isinstance(img_id, str) and img_id.strip():
            sanitized_ids.append(img_id.strip())

    if not sanitized_ids:
        raise ValueError("No valid image IDs provided")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Efficient single query with parameterized IN clause
        if sanitized_ids:
            # Generate placeholders safely based on list length
            placeholders = ",".join(["?"] * len(sanitized_ids))
            query = f"SELECT id FROM images WHERE id IN ({placeholders})"
            cursor.execute(query, sanitized_ids)  # Pass string IDs directly
            valid_images = [row[0] for row in cursor.fetchall()]
        else:
            valid_images = []

        if not valid_images:
            raise ValueError("None of the provided image IDs exist in the database.")

        # Insert into album_images using executemany
        cursor.executemany(
            "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
            [(album_id, img_id) for img_id in valid_images],
        )
        conn.commit()

        
def db_remove_image_from_album(album_id: str, image_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM album_images WHERE album_id = ? AND image_id = ?",
            (album_id, image_id),
        )
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
                (album_id, image_id),
            )
        else:
            raise ValueError("Image not found in the specified album")


def db_remove_images_from_album(album_id: str, image_ids: list[str]):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.executemany(
            "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
            [(album_id, img_id) for img_id in image_ids],
        )
        conn.commit()
    finally:
        conn.close()


def verify_album_password(album_id: str, password: str) -> bool:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT password_hash FROM albums WHERE album_id = ?", (album_id,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8"))
    finally:
        conn.close()
