import sqlite3
import bcrypt
from typing import List, Tuple, Optional
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def _connect() -> sqlite3.Connection:
    """Helper to establish database connection with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def db_create_albums_table() -> None:
    """
    Creates the albums and album_media tables.
    Refactored to support cover images, timestamps, and mixed media (video/image).
    """
    conn = _connect()
    cursor = conn.cursor()
    try:
        # 1. Create Albums Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_id TEXT PRIMARY KEY,
            album_name TEXT UNIQUE NOT NULL,
            description TEXT,
            cover_image_id TEXT,
            is_hidden BOOLEAN DEFAULT 0,
            password_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cover_image_id) REFERENCES images(id) ON DELETE SET NULL
        );
        """)

        # 2. Create Album Media Junction Table (Replaces album_images)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS album_media (
            id TEXT PRIMARY KEY,
            album_id TEXT NOT NULL,
            media_id TEXT NOT NULL,
            media_type TEXT NOT NULL CHECK(media_type IN ('image', 'video')),
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
            FOREIGN KEY (media_id) REFERENCES images(id) ON DELETE CASCADE,
            UNIQUE(album_id, media_id)
        );
        """)
        
        conn.commit()
        logger.info("Albums and Album_Media tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Error creating albums table: {e}")
    finally:
        conn.close()

# --- CRUD Operations ---

def db_get_all_albums(show_hidden: bool = False) -> List[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM albums"
        if not show_hidden:
            query += " WHERE is_hidden = 0"
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def db_get_album(album_id: str) -> Optional[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM albums WHERE album_id = ?", (album_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def db_get_album_by_name(name: str) -> Optional[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM albums WHERE album_name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def db_insert_album(
    album_id: str,
    album_name: str,
    description: str = "",
    cover_image_id: Optional[str] = None,
    is_hidden: bool = False,
    password: str = None,
) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    try:
        if cover_image_id:
            # We add "AND media_type = 'image'" to ensure it's not a video
            cursor.execute("SELECT 1 FROM images WHERE id = ? AND media_type = 'image'", (cover_image_id,))
            if not cursor.fetchone():
                logger.error(f"Invalid cover_image_id (or not an image): {cover_image_id}")
                return False
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            
        cursor.execute(
            """
            INSERT INTO albums (album_id, album_name, description, cover_image_id, is_hidden, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (album_id, album_name, description, cover_image_id, int(is_hidden), password_hash),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"Album creation failed (duplicate name?): {e}")
        return False
    finally:
        conn.close()

def db_update_album(
    album_id: str, 
    album_name: str, 
    description: str, 
    cover_image_id: Optional[str], 
    is_hidden: bool, 
    password: Optional[str] = None
) -> bool:
    """
    Updates album details.
    - password=None: Do not change the password.
    - password="": Remove the password (make public).
    - password="str": Update/Set the password.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    if cover_image_id:
        cursor.execute("SELECT 1 FROM images WHERE id = ? AND media_type = 'image'", (cover_image_id,))
        if not cursor.fetchone():
            logger.error(f"Cannot update album {album_id}: Invalid cover_image_id or not an image {cover_image_id}")
            conn.close()
            return False
    # Base fields to update
    updates = [
        "album_name = ?",
        "description = ?",
        "cover_image_id = ?",
        "is_hidden = ?",
        "updated_at = CURRENT_TIMESTAMP"
    ]
    params = [album_name, description, cover_image_id, is_hidden]

    # Handle Password Logic
    if password == "":
        # Case: Remove password protection
        updates.append("password_hash = NULL")
    elif password:
        # Case: Update/Set new password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        updates.append("password_hash = ?")
        params.append(hashed)
    # Case: password is None -> Do nothing (keep existing)

    params.append(album_id) # Add ID for the WHERE clause
    
    query = f"UPDATE albums SET {', '.join(updates)} WHERE album_id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating album {album_id}: {e}")
        return False
    finally:
        conn.close()

def db_delete_album(album_id: str) -> bool:
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))
        rows_affected = cursor.rowcount 
        conn.commit()
        return rows_affected > 0
    finally:
        conn.close()

# --- Media Operations (Images & Videos) ---

def db_get_album_media(album_id: str) -> List[dict]:
    """Returns a list of media items (id, type) for the album."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT media_id, media_type, added_at 
            FROM album_media 
            WHERE album_id = ? 
            ORDER BY sort_order ASC, added_at DESC
            """, 
            (album_id,)
        )
        rows = cursor.fetchall() 
        return [dict(row) for row in rows]
    finally:
        conn.close()

def db_add_media_to_album(album_id: str, media_items: List[Tuple[str, str]]) -> int:
    """Adds a list of (media_id, media_type) to the album."""
    conn = _connect()
    cursor = conn.cursor()
    count = 0
    try:
        # 1. FIX: Explicitly check if album exists first
        cursor.execute("SELECT 1 FROM albums WHERE album_id = ?", (album_id,))
        if not cursor.fetchone():
            logger.error(f"Album {album_id} not found.")
            return 0

        # Get current max sort order
        cursor.execute("SELECT MAX(sort_order) FROM album_media WHERE album_id = ?", (album_id,))
        result = cursor.fetchone()
        current_max_sort = result[0] if result[0] is not None else 0

        for i, (media_id, media_type) in enumerate(media_items):
            if media_type not in ('image', 'video'):
                logger.warning(f"Skipping invalid media_type: {media_type}")
                continue
            cursor.execute("SELECT 1 FROM images WHERE id = ? AND media_type = ?", (media_id, media_type))
            
            if not cursor.fetchone():
                logger.warning(f"Skipping invalid media_id or mismatched type: {media_id} ({media_type})")
                continue

            junction_id = f"{album_id}_{media_id}"
            
            try:
                cursor.execute(
                    "INSERT INTO album_media (id, album_id, media_id, media_type, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (junction_id, album_id, media_id, media_type, current_max_sort + i + 1)
                )
                count += 1
            except sqlite3.IntegrityError:
                # 3. FIX: Now we know this is strictly a DUPLICATE entry (Unique Constraint),
                # because we already verified the Album and Media IDs exist.
                continue 
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error adding media to album: {e}")
        return 0
    finally:
        conn.close()
    
    return count

def db_remove_media_from_album(album_id: str, media_id: str) -> None:
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM album_media WHERE album_id = ? AND media_id = ?",
            (album_id, media_id),
        )
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