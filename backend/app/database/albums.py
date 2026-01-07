import bcrypt
from typing import List, Optional, Tuple

from app.database.connection import (
    get_db_connection,
    get_db_transaction,
    get_db_write_transaction,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def db_create_albums_table() -> None:
    """Create the albums table if it doesn't exist."""
    with get_db_transaction() as conn:
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


def db_create_album_images_table() -> None:
    """Create the album_images junction table if it doesn't exist."""
    with get_db_transaction() as conn:
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


def db_get_all_albums(show_hidden: bool = False) -> List[Tuple]:
    """
    Get all albums from the database.

    Args:
        show_hidden: Whether to include hidden albums

    Returns:
        List of album tuples
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if show_hidden:
            cursor.execute("SELECT * FROM albums")
        else:
            cursor.execute("SELECT * FROM albums WHERE is_hidden = 0")
        return cursor.fetchall()


def db_get_album_by_name(name: str) -> Optional[Tuple]:
    """
    Get an album by its name.

    Args:
        name: Album name to search for

    Returns:
        Album tuple if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM albums WHERE album_name = ?", (name,))
        album = cursor.fetchone()
        return album if album else None


def db_get_album(album_id: str) -> Optional[Tuple]:
    """
    Get an album by its ID.

    Args:
        album_id: Album ID to search for

    Returns:
        Album tuple if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM albums WHERE album_id = ?", (album_id,))
        album = cursor.fetchone()
        return album if album else None


def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    is_hidden: bool = False,
    password: str = None,
) -> None:
    """
    Insert a new album into the database.

    Args:
        album_id: Unique album ID
        album_name: Album name
        description: Album description
        is_hidden: Whether the album is hidden
        password: Optional password for protected albums
    """
    with get_db_write_transaction() as conn:
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


def db_update_album(
    album_id: str,
    album_name: str,
    description: str,
    is_hidden: bool,
    password: str = None,
) -> None:
    """
    Update an existing album.

    Args:
        album_id: Album ID to update
        album_name: New album name
        description: New description
        is_hidden: New hidden status
        password: New password (None to keep existing)
    """
    with get_db_write_transaction() as conn:
        cursor = conn.cursor()
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


def db_delete_album(album_id: str) -> None:
    """
    Delete an album from the database.

    Args:
        album_id: Album ID to delete
    """
    with get_db_write_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))


def db_get_album_images(album_id: str) -> List[str]:
    """
    Get all image IDs in an album.

    Args:
        album_id: Album ID to get images for

    Returns:
        List of image IDs
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT image_id FROM album_images WHERE album_id = ?", (album_id,)
        )
        images = cursor.fetchall()
        return [img[0] for img in images]


def db_add_images_to_album(album_id: str, image_ids: List[str]) -> None:
    """
    Add images to an album.

    Args:
        album_id: Album ID to add images to
        image_ids: List of image IDs to add

    Raises:
        ValueError: If none of the provided image IDs exist
    """
    with get_db_write_transaction() as conn:
        cursor = conn.cursor()

        query = (
            f"SELECT id FROM images WHERE id IN ({','.join('?' for _ in image_ids)})"
        )
        cursor.execute(query, image_ids)
        valid_images = [row[0] for row in cursor.fetchall()]

        if valid_images:
            cursor.executemany(
                "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
                [(album_id, img_id) for img_id in valid_images],
            )
        else:
            raise ValueError("None of the provided image IDs exist in the database.")


def db_remove_image_from_album(album_id: str, image_id: str) -> None:
    """
    Remove a single image from an album.

    Args:
        album_id: Album ID to remove image from
        image_id: Image ID to remove

    Raises:
        ValueError: If the image is not in the album
    """
    with get_db_write_transaction() as conn:
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


def db_remove_images_from_album(album_id: str, image_ids: List[str]) -> None:
    """
    Remove multiple images from an album.

    Args:
        album_id: Album ID to remove images from
        image_ids: List of image IDs to remove
    """
    with get_db_write_transaction() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
            [(album_id, img_id) for img_id in image_ids],
        )


def verify_album_password(album_id: str, password: str) -> bool:
    """
    Verify the password for a protected album.

    Args:
        album_id: Album ID to verify password for
        password: Password to verify

    Returns:
        True if password is correct, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM albums WHERE album_id = ?", (album_id,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8"))
