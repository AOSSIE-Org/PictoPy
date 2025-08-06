import sqlite3
import os
import uuid
from typing import List, Tuple, Dict, Optional
from app.config.settings import DATABASE_PATH

# Type definitions
FolderId = str
FolderPath = str
FolderData = Tuple[FolderId, FolderPath, Optional[FolderId], int, bool, Optional[bool]]
FolderMap = Dict[FolderPath, Tuple[FolderId, Optional[FolderId]]]
FolderIdPath = Tuple[FolderId, str]


def db_create_folders_table() -> None:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS folders (
            folder_id TEXT PRIMARY KEY,
            parent_folder_id TEXT,
            folder_path TEXT UNIQUE,
            last_modified_time INTEGER,
            AI_Tagging BOOLEAN,
            taggingCompleted BOOLEAN,
            FOREIGN KEY (parent_folder_id) REFERENCES folders(folder_id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def db_insert_folders_batch(folders_data: List[FolderData]) -> None:
    """
    Insert multiple folders in a single database transaction.
    folders_data: list of tuples (folder_id, folder_path,
    parent_folder_id,last_modified_time, AI_Tagging, taggingCompleted)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """INSERT OR IGNORE INTO folders (folder_id, folder_path, parent_folder_id, last_modified_time, AI_Tagging, taggingCompleted) VALUES (?, ?, ?, ?, ?, ?)""",
            folders_data,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def db_insert_folder(
    folder_path: FolderPath,
    parent_folder_id: Optional[FolderId] = None,
    AI_Tagging: bool = False,
    taggingCompleted: Optional[bool] = None,
    folder_id: Optional[FolderId] = None,
) -> FolderId:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    abs_folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(abs_folder_path):
        raise ValueError(f"Error: '{folder_path}' is not a valid directory.")

    cursor.execute(
        "SELECT folder_id FROM folders WHERE folder_path = ?",
        (abs_folder_path,),
    )
    existing_folder = cursor.fetchone()

    if existing_folder:
        result = existing_folder[0]
        conn.close()
        return result

    # Time is in Unix format
    last_modified_time = int(os.path.getmtime(abs_folder_path))

    if folder_id is None:
        folder_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO folders (folder_id, folder_path, parent_folder_id, last_modified_time, AI_Tagging, taggingCompleted) VALUES (?, ?, ?, ?, ?, ?)",
        (
            folder_id,
            abs_folder_path,
            parent_folder_id,
            last_modified_time,
            AI_Tagging,
            taggingCompleted,
        ),
    )

    conn.commit()
    conn.close()
    return folder_id


def db_get_folder_id_from_path(folder_path: FolderPath) -> Optional[FolderId]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_folder_path = os.path.abspath(folder_path)
    cursor.execute(
        "SELECT folder_id FROM folders WHERE folder_path = ?",
        (abs_folder_path,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def db_get_folder_path_from_id(folder_id: FolderId) -> Optional[FolderPath]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT folder_path FROM folders WHERE folder_id = ?",
        (folder_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def db_get_all_folders() -> List[FolderPath]:
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute("SELECT folder_path FROM folders").fetchall()
        return [row[0] for row in rows] if rows else []


def db_get_all_folder_ids() -> List[FolderId]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id from folders")
    rows = cursor.fetchall()
    return [row[0] for row in rows] if rows else []


def db_delete_folders_batch(folder_ids: List[FolderId]) -> int:
    """
    Delete multiple folders in a single database transaction.
    folder_ids: list of folder IDs to delete
    Returns the number of folders deleted
    """
    if not folder_ids:
        return 0

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Enable foreign keys for cascading deletes
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        # Create placeholders for the IN clause
        placeholders = ",".join("?" * len(folder_ids))

        cursor.execute(
            f"DELETE FROM folders WHERE folder_id IN ({placeholders})",
            folder_ids,
        )

        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def db_delete_folder(folder_path: FolderPath) -> None:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_folder_path = os.path.abspath(folder_path)
    cursor.execute(
        "PRAGMA foreign_keys = ON;"
    )  # Important for deleting rows in image_id_mapping and images table because they reference this folder_id
    conn.commit()
    cursor.execute(
        "SELECT folder_id FROM folders WHERE folder_path = ?",
        (abs_folder_path,),
    )
    existing_folder = cursor.fetchone()

    if not existing_folder:
        conn.close()
        raise ValueError(
            f"Error: Folder '{folder_path}' does not exist in the database."
        )

    cursor.execute(
        "DELETE FROM folders WHERE folder_path = ?",
        (abs_folder_path,),
    )

    conn.commit()
    conn.close()


def db_update_parent_ids_for_subtree(
    root_folder_path: FolderPath, folder_map: FolderMap
) -> None:
    """
    Update parent_folder_id for all folders in the subtree rooted at root_folder_path.
    Only updates folders whose parent_folder_id is NULL.
    folder_map: dict mapping folder_path to tuple of (folder_id, parent_id)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        for folder_path, (folder_id, parent_id) in folder_map.items():
            if parent_id:
                cursor.execute(
                    """
                    UPDATE folders
                    SET parent_folder_id = ?
                    WHERE folder_path = ? AND parent_folder_id IS NULL
                    """,
                    (parent_id, folder_path),
                )
        conn.commit()
    finally:
        conn.close()


def db_folder_exists(folder_path: FolderPath) -> bool:
    """
    Check if a folder exists in the database.
    Returns True if the folder exists, False otherwise.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        abs_path = os.path.abspath(folder_path)
        cursor.execute(
            "SELECT folder_id FROM folders WHERE folder_path = ?", (abs_path,)
        )
        result = cursor.fetchone()
        return bool(result)
    finally:
        conn.close()


def db_find_parent_folder_id(folder_path: FolderPath) -> Optional[FolderId]:
    """
    Find the folder_id of the parent folder by checking if the parent path exists in the DB.
    Returns the parent folder_id if found, None otherwise.
    """
    parent_path = os.path.dirname(folder_path)
    if not parent_path or parent_path == folder_path:  # Root directory
        return None

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT folder_id FROM folders WHERE folder_path = ?", (parent_path,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def db_update_ai_tagging_batch(
    folder_ids: List[FolderId], ai_tagging_enabled: bool
) -> int:
    """
    Update AI_Tagging status for multiple folders in a single transaction.
    folder_ids: list of folder IDs to update
    ai_tagging_enabled: boolean value to set for AI_Tagging
    Returns the number of folders updated
    """
    if not folder_ids:
        return 0

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Create placeholders for the IN clause
        placeholders = ",".join("?" * len(folder_ids))

        cursor.execute(
            f"UPDATE folders SET AI_Tagging = ? WHERE folder_id IN ({placeholders})",
            [ai_tagging_enabled] + folder_ids,
        )

        updated_count = cursor.rowcount
        conn.commit()
        return updated_count
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def db_enable_ai_tagging_batch(folder_ids: List[FolderId]) -> int:
    """
    Enable AI tagging for multiple folders.
    folder_ids: list of folder IDs to enable AI tagging for
    Returns the number of folders updated
    """
    return db_update_ai_tagging_batch(folder_ids, True)


def db_disable_ai_tagging_batch(folder_ids: List[FolderId]) -> int:
    """
    Disable AI tagging for multiple folders.
    folder_ids: list of folder IDs to disable AI tagging for
    Returns the number of folders updated
    """
    return db_update_ai_tagging_batch(folder_ids, False)


def db_get_folder_ids_by_path_prefix(root_path: str) -> List[FolderIdPath]:
    """Get all folder IDs and paths whose path starts with the given root path."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Use path LIKE with wildcard to match all subfolders
        cursor.execute(
            """
            SELECT folder_id, folder_path FROM folders 
            WHERE folder_path LIKE ? || '%'
        """,
            (root_path,),
        )

        return cursor.fetchall()
    finally:
        conn.close()


def db_get_direct_child_folders(parent_folder_id: str) -> List[Tuple[str, str]]:
    """
    Get all direct child folders (not subfolders) for a given parent folder.
    Returns list of tuples (folder_id, folder_path).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT folder_id, folder_path FROM folders 
            WHERE parent_folder_id = ?
        """,
            (parent_folder_id,),
        )

        return cursor.fetchall()
    finally:
        conn.close()
