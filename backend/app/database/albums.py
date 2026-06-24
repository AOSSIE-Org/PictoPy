import sqlite3

import bcrypt

from app.database.connection import get_db_connection
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def db_create_albums_table() -> None:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS albums (
                    album_id TEXT PRIMARY KEY,
                    album_name TEXT UNIQUE,
                    description TEXT,
                    is_hidden BOOLEAN DEFAULT 0,
                    password_hash TEXT
                )
                """)
    except sqlite3.Error as e:
        logger.error(f"Error creating albums table: {e}")
        raise


def db_create_album_images_table() -> None:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS album_images (
                    album_id TEXT,
                    image_id TEXT,
                    PRIMARY KEY (album_id, image_id),
                    FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
                    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
                )
                """)
    except sqlite3.Error as e:
        logger.error(f"Error creating album_images table: {e}")
        raise


def db_get_all_albums(show_hidden: bool = False) -> list[tuple]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if show_hidden:
                cursor.execute("SELECT * FROM albums")
            else:
                cursor.execute("SELECT * FROM albums WHERE is_hidden = 0")
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error getting all albums: {e}")
        raise


def db_get_album_by_name(name: str) -> tuple | None:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM albums WHERE album_name = ?", (name,))
            album = cursor.fetchone()
            return album if album else None
    except sqlite3.Error as e:
        logger.error(f"Error getting album by name '{name}': {e}")
        raise


def db_get_album(album_id: str) -> tuple | None:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM albums WHERE album_id = ?", (album_id,))
            album = cursor.fetchone()
            return album if album else None
    except sqlite3.Error as e:
        logger.error(f"Error getting album '{album_id}': {e}")
        raise


def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    is_hidden: bool = False,
    password: str | None = None,
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
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
    except sqlite3.Error as e:
        logger.error(f"Error inserting album '{album_name}': {e}")
        raise


def db_update_album(
    album_id: str,
    album_name: str,
    description: str,
    is_hidden: bool,
    password: str | None = None,
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if password is not None:
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
                cursor.execute(
                    """
                    UPDATE albums
                    SET album_name = ?, description = ?, is_hidden = ?
                    WHERE album_id = ?
                    """,
                    (album_name, description, int(is_hidden), album_id),
                )
    except sqlite3.Error as e:
        logger.error(f"Error updating album '{album_id}': {e}")
        raise


def db_delete_album(album_id: str):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))
    except sqlite3.Error as e:
        logger.error(f"Error deleting album '{album_id}': {e}")
        raise


def db_get_album_images(album_id: str):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT image_id FROM album_images WHERE album_id = ?", (album_id,)
            )
            images = cursor.fetchall()
            return [img[0] for img in images]
    except sqlite3.Error as e:
        logger.error(f"Error getting images for album '{album_id}': {e}")
        raise


def db_add_images_to_album(album_id: str, image_ids: list[str]):
    if not isinstance(image_ids, list):
        raise TypeError("image_ids must be a list of IDs")

    sanitized_ids = []
    for img_id in image_ids:
        if isinstance(img_id, str) and img_id.strip():
            sanitized_ids.append(img_id.strip())

    if not sanitized_ids:
        raise ValueError("No valid image IDs provided")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            placeholders = ",".join(["?"] * len(sanitized_ids))
            query = f"SELECT id FROM images WHERE id IN ({placeholders})"
            cursor.execute(query, sanitized_ids)
            valid_images = [row[0] for row in cursor.fetchall()]

            if not valid_images:
                raise ValueError(
                    "None of the provided image IDs exist in the database."
                )

            cursor.executemany(
                "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
                [(album_id, img_id) for img_id in valid_images],
            )
    except sqlite3.Error as e:
        logger.error(f"Error adding images to album '{album_id}': {e}")
        raise


def db_remove_image_from_album(album_id: str, image_id: str):
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Error removing image '{image_id}' from album '{album_id}': {e}")
        raise


def db_remove_images_from_album(album_id: str, image_ids: list[str]):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
                [(album_id, img_id) for img_id in image_ids],
            )
    except sqlite3.Error as e:
        logger.error(f"Error removing images from album '{album_id}': {e}")
        raise


def verify_album_password(album_id: str, password: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash FROM albums WHERE album_id = ?", (album_id,)
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return False
            return bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8"))
    except sqlite3.Error as e:
        logger.error(f"Error verifying password for album '{album_id}': {e}")
        raise
