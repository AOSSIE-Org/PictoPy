import sqlite3
from contextlib import contextmanager

import bcrypt

from app.database.connection import get_db_connection
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


@contextmanager
def logged_db_connection(action: str):
    try:
        with get_db_connection() as conn:
            yield conn
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity Error {action}: {e}")
        raise
    except sqlite3.OperationalError as e:
        logger.error(f"Operational Error {action}: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Database Error {action}: {e}")
        raise


def db_create_albums_table() -> None:
    with logged_db_connection("creating albums table") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS albums (
                album_id TEXT PRIMARY KEY,
                album_name TEXT UNIQUE,
                description TEXT,
                is_locked BOOLEAN DEFAULT 0,
                password_hash TEXT,
                cover_image_path TEXT
            )
            """
        )
        # Shipped databases predate the is_hidden -> is_locked rename and the
        # cover_image_path column, and CREATE IF NOT EXISTS won't add either.
        cursor.execute("PRAGMA table_info(albums)")
        columns = {row[1] for row in cursor.fetchall()}
        if "is_locked" not in columns and "is_hidden" in columns:
            cursor.execute("ALTER TABLE albums RENAME COLUMN is_hidden TO is_locked")
        if "cover_image_path" not in columns:
            cursor.execute("ALTER TABLE albums ADD COLUMN cover_image_path TEXT")


def db_create_album_images_table() -> None:
    with logged_db_connection("creating album_images table") as conn:
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
        # The PK leads with album_id, so lookup by image alone needs its own
        # index. The memory scorer does exactly that, per image.
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_album_images_image_id "
            "ON album_images(image_id)"
        )


def db_get_all_albums() -> list[tuple]:
    """Get all albums (both locked and unlocked)."""
    with logged_db_connection("getting all albums") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT album_id, album_name, description, is_locked, password_hash, cover_image_path FROM albums"
        )
        return cursor.fetchall()


def db_get_album_by_name(name: str) -> tuple | None:
    with logged_db_connection(f"getting album by name '{name}'") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT album_id, album_name, description, is_locked, password_hash, cover_image_path FROM albums WHERE album_name = ?",
            (name,),
        )
        album = cursor.fetchone()
        return album if album else None


def db_get_album(album_id: str) -> tuple | None:
    with logged_db_connection(f"getting album '{album_id}'") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT album_id, album_name, description, is_locked, password_hash, cover_image_path FROM albums WHERE album_id = ?",
            (album_id,),
        )
        album = cursor.fetchone()
        return album if album else None


def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    is_locked: bool = False,
    password: str | None = None,
):
    with logged_db_connection(f"inserting album '{album_name}'") as conn:
        cursor = conn.cursor()
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        cursor.execute(
            """
            INSERT INTO albums (album_id, album_name, description, is_locked, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (album_id, album_name, description, int(is_locked), password_hash),
        )


def db_update_album(
    album_id: str,
    album_name: str,
    description: str,
    is_locked: bool,
    password: str | None = None,
):
    with logged_db_connection(f"updating album '{album_id}'") as conn:
        cursor = conn.cursor()
        if password is not None:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_locked = ?, password_hash = ?
                WHERE album_id = ?
                """,
                (album_name, description, int(is_locked), password_hash, album_id),
            )
        else:
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_locked = ?
                WHERE album_id = ?
                """,
                (album_name, description, int(is_locked), album_id),
            )


def db_delete_album(album_id: str):
    with logged_db_connection(f"deleting album '{album_id}'") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))


def db_update_album_cover_image(album_id: str, cover_image_path: str):
    """Update the cover image path for an album"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE albums SET cover_image_path = ? WHERE album_id = ?",
            (cover_image_path, album_id),
        )
        conn.commit()
    finally:
        conn.close()


def db_get_album_images(album_id: str):
    with logged_db_connection(f"getting images for album '{album_id}'") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT image_id FROM album_images WHERE album_id = ?", (album_id,)
        )
        images = cursor.fetchall()
        return [img[0] for img in images]


def db_add_images_to_album(album_id: str, image_ids: list[str]):
    if not isinstance(image_ids, list):
        raise TypeError("image_ids must be a list of IDs")

    sanitized_ids = []
    for img_id in image_ids:
        if isinstance(img_id, str) and img_id.strip():
            sanitized_ids.append(img_id.strip())

    if not sanitized_ids:
        raise ValueError("No valid image IDs provided")

    with logged_db_connection(f"adding images to album '{album_id}'") as conn:
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(sanitized_ids))
        query = f"SELECT id FROM images WHERE id IN ({placeholders})"
        cursor.execute(query, sanitized_ids)
        valid_images = [row[0] for row in cursor.fetchall()]

        if not valid_images:
            raise ValueError("None of the provided image IDs exist in the database.")

        cursor.executemany(
            "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
            [(album_id, img_id) for img_id in valid_images],
        )


def db_remove_image_from_album(album_id: str, image_id: str):
    with logged_db_connection(
        f"removing image '{image_id}' from album '{album_id}'"
    ) as conn:
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
            raise ValueError("[Mapped 404] Image not found in the specified album")


def db_remove_images_from_album(album_id: str, image_ids: list[str]):
    with logged_db_connection(f"removing images from album '{album_id}'") as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
            [(album_id, img_id) for img_id in image_ids],
        )


def verify_album_password(album_id: str, password: str) -> bool:
    with logged_db_connection(f"verifying password for album '{album_id}'") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM albums WHERE album_id = ?", (album_id,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8"))

def db_get_image_path(image_id: str) -> str | None:
    """Get the path of an image by its ID."""
    with logged_db_connection(f"getting path for image '{image_id}'") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM images WHERE id = ?", (image_id,))
        result = cursor.fetchone()
        return result[0] if result else None
