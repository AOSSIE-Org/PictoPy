import sqlite3
from typing import Any, List, Optional, Tuple, TypedDict

import bcrypt
from app.config.settings import DATABASE_PATH
from app.database.connection import get_db_connection


class AlbumRow(TypedDict):
    """A row of the albums table, as the read helpers below return it."""

    album_id: str
    album_name: str
    description: Optional[str]
    is_locked: bool
    password_hash: Optional[str]
    cover_image_path: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    # Ensure ON DELETE CASCADE and other FKs are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Named once so the SELECTs and the mapper below cannot drift apart.
_ALBUM_COLUMNS = (
    "album_id, album_name, description, is_locked, "
    "password_hash, cover_image_path, created_at, updated_at"
)

# Built once from the column list rather than interpolated at each call site.
_SELECT_ALL_ALBUMS = f"SELECT {_ALBUM_COLUMNS} FROM albums ORDER BY rowid"
_SELECT_ALBUM_BY_NAME = f"SELECT {_ALBUM_COLUMNS} FROM albums WHERE album_name = ?"
_SELECT_ALBUM_BY_ID = f"SELECT {_ALBUM_COLUMNS} FROM albums WHERE album_id = ?"


def _to_album_row(row: Tuple[Any, ...]) -> AlbumRow:
    """Map a SELECT of _ALBUM_COLUMNS onto a named record."""
    return AlbumRow(
        album_id=row[0],
        album_name=row[1],
        description=row[2],
        is_locked=bool(row[3]),
        password_hash=row[4],
        cover_image_path=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def db_create_albums_table() -> None:
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS albums (
                album_id TEXT PRIMARY KEY,
                album_name TEXT UNIQUE,
                description TEXT,
                is_locked BOOLEAN DEFAULT 0,
                password_hash TEXT,
                cover_image_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Shipped databases predate the is_hidden -> is_locked rename and the
        # cover_image_path and created_at columns, and CREATE IF NOT EXISTS
        # won't add any of them.
        cursor.execute("PRAGMA table_info(albums)")
        columns = {row[1] for row in cursor.fetchall()}
        if "is_locked" not in columns and "is_hidden" in columns:
            cursor.execute("ALTER TABLE albums RENAME COLUMN is_hidden TO is_locked")
        if "cover_image_path" not in columns:
            cursor.execute("ALTER TABLE albums ADD COLUMN cover_image_path TEXT")
        if "created_at" not in columns:
            # No default: SQLite rejects a non-constant one here, and the upgrade
            # time is a date that never happened. NULL reads as oldest, which
            # insertion order already reflects.
            cursor.execute("ALTER TABLE albums ADD COLUMN created_at DATETIME")
        if "updated_at" not in columns:
            cursor.execute("ALTER TABLE albums ADD COLUMN updated_at DATETIME")
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def db_create_album_images_table() -> None:
    conn = None
    try:
        conn = _connect()
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
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def _touch_album(cursor: sqlite3.Cursor, album_id: str) -> None:
    """
    Mark an album as changed just now.

    Adding or removing photos counts: to a user, that is the album changing,
    not just its name or its lock.
    """
    cursor.execute(
        "UPDATE albums SET updated_at = CURRENT_TIMESTAMP WHERE album_id = ?",
        (album_id,),
    )


def db_get_all_albums() -> List[AlbumRow]:
    """Get all albums (both locked and unlocked)."""
    conn = _connect()
    cursor = conn.cursor()
    try:
        # Insertion order, so albums predating created_at keep the order they
        # were made in rather than an arbitrary one.
        cursor.execute(_SELECT_ALL_ALBUMS)
        return [_to_album_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def db_get_album_by_name(name: str) -> Optional[AlbumRow]:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(_SELECT_ALBUM_BY_NAME, (name,))
        album = cursor.fetchone()
        return _to_album_row(album) if album else None
    finally:
        conn.close()


def db_get_album(album_id: str) -> Optional[AlbumRow]:
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(_SELECT_ALBUM_BY_ID, (album_id,))
        album = cursor.fetchone()
        return _to_album_row(album) if album else None
    finally:
        conn.close()


def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    is_locked: bool = False,
    password: Optional[str] = None,
):
    conn = _connect()
    cursor = conn.cursor()
    try:
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        # created_at is set here rather than left to the column default: a
        # database migrated with ALTER TABLE has no default to fall back on.
        cursor.execute(
            """
            INSERT INTO albums (
                album_id, album_name, description, is_locked,
                password_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (album_id, album_name, description, int(is_locked), password_hash),
        )
        conn.commit()
    finally:
        conn.close()


def db_create_album_with_images(
    album_id: str, album_name: str, description: str, image_ids: list[str]
) -> int:
    """
    Create an album and link its images in a single transaction.

    Both halves commit together, so a failed link never strands an empty album.
    Takes image ids rather than the id of whatever they came from, so the
    caller owns that choice. Returns the number of images actually linked.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO albums (
                album_id, album_name, description, is_locked,
                password_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, 0, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (album_id, album_name, description),
        )
        # Foreign keys are on for this connection, so an image id that no
        # longer exists rolls the album back with it rather than half-writing.
        cursor.executemany(
            "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
            [(album_id, image_id) for image_id in image_ids],
        )
        return cursor.rowcount


def db_update_album(
    album_id: str,
    album_name: str,
    description: str,
    is_locked: bool,
    password: Optional[str] = None,
):
    conn = _connect()
    cursor = conn.cursor()
    try:
        if password is not None:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_locked = ?, password_hash = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE album_id = ?
                """,
                (album_name, description, int(is_locked), password_hash, album_id),
            )
        else:
            cursor.execute(
                """
                UPDATE albums
                SET album_name = ?, description = ?, is_locked = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE album_id = ?
                """,
                (album_name, description, int(is_locked), album_id),
            )
        conn.commit()
    finally:
        conn.close()


def db_delete_album(album_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))


def db_get_album_cover_path(album_id: str) -> str | None:
    """Path of the album's cover: its first image, by insertion order."""
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT images.path
            FROM album_images
            JOIN images ON images.id = album_images.image_id
            WHERE album_images.album_id = ?
            ORDER BY album_images.rowid
            LIMIT 1
            """,
            (album_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def db_get_album_images(album_id: str):
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT image_id FROM album_images WHERE album_id = ?", (album_id,)
        )
        images = cursor.fetchall()
        return [img[0] for img in images]
    finally:
        conn.close()


def db_count_album_images(album_id: str) -> int:
    """How many images an album holds, without reading every id."""
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM album_images WHERE album_id = ?", (album_id,)
        )
        return int(cursor.fetchone()[0])
    finally:
        conn.close()


def db_album_contains_image(album_id: str, image_id: str) -> bool:
    """
    Whether one image belongs to an album.

    Kept separate from db_get_album_images because callers on a request path
    need a single membership answer, not every id in the album.
    """
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM album_images WHERE album_id = ? AND image_id = ? LIMIT 1",
            (album_id, image_id),
        )
        return cursor.fetchone() is not None
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

        placeholders = ",".join(["?"] * len(sanitized_ids))
        query = f"SELECT id FROM images WHERE id IN ({placeholders})"
        cursor.execute(query, sanitized_ids)  # Pass string IDs directly
        valid_images = [row[0] for row in cursor.fetchall()]

        if not valid_images:
            raise ValueError("None of the provided image IDs exist in the database.")

        cursor.executemany(
            "INSERT OR IGNORE INTO album_images (album_id, image_id) VALUES (?, ?)",
            [(album_id, img_id) for img_id in valid_images],
        )
        # Every id may already be in the album, in which case OR IGNORE writes
        # nothing and the album has not actually changed. Read before touching:
        # the touch overwrites rowcount.
        if cursor.rowcount:
            _touch_album(cursor, album_id)
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
            _touch_album(cursor, album_id)
        else:
            raise ValueError("Image not found in the specified album")


def db_remove_images_from_album(album_id: str, image_ids: list[str]):
    conn = _connect()
    cursor = conn.cursor()
    try:
        cursor.executemany(
            "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
            [(album_id, img_id) for img_id in image_ids],
        )
        # Same as the insert: ids that were not in the album delete nothing.
        if cursor.rowcount:
            _touch_album(cursor, album_id)
        conn.commit()
    finally:
        conn.close()


def verify_album_password(album_id: str, password: str) -> bool:
    conn = _connect()
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
