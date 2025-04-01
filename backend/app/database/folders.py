import sqlite3
import os
from typing import Optional
from app.config.settings import DATABASE_PATH


def create_folders_table() -> None:
    """
    Create folders table if it does not exists

    Returns:
        None: Creates table and returns nothing.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS folders (
            folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT UNIQUE,
            last_modified_time INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def insert_folder(folder_path: str) -> int | None:
    """
    Inserts a folder path into the 'folders' table if it does not already exist.

    Args:
        folder_path (str): The absolute or relative path to the folder to be inserted.

    Returns:
        str | None: The folder ID if the folder exists or is successfully inserted,
        otherwise None if the insertion fails or no folder is found.
    """
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
        return int(result)

    # Time is in Unix format
    last_modified_time = int(os.path.getmtime(abs_folder_path))

    cursor.execute(
        "INSERT INTO folders (folder_path, last_modified_time) VALUES (?, ?)",
        (abs_folder_path, last_modified_time),
    )

    conn.commit()

    cursor.execute(
        "SELECT folder_id FROM folders WHERE folder_path = ?",
        (abs_folder_path,),
    )
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def get_folder_id_from_path(folder_path: str) -> Optional[int]:
    """
    Retrieves the folder ID from the database for the given folder path.

    Args:
        folder_path (str): The absolute or relative folder path to query.

    Returns:
        Optional[str]: The folder ID if found, otherwise None.
    """
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


def get_folder_path_from_id(folder_id: str) -> Optional[str]:
    """
    Retrieves the folder path from the database for the given folder id.

    Args:
        folder_id (str): The folder id for query.

    Returns:
        Optional[str]: The folder path if found, otherwise None.
    """

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT folder_path FROM folders WHERE folder_id = ?",
        (folder_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_all_folders() -> list[str]:
    """
    Retrieves the all the folder paths from the database

    Returns:
        list[str]: list of all folder paths or an empty list if no folders.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute("SELECT folder_path FROM folders").fetchall()
        return [row[0] for row in rows] if rows else []


def get_all_folder_ids() -> list[int]:
    """
    Retrieves all the folder IDs from the database

    Returns:
        list[str]: list of all folder ids or an empty list if no folders.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id from folders")
    rows = cursor.fetchall()
    return [row[0] for row in rows] if rows else []


def delete_folder(folder_path: str) -> None:
    """ "
    Deletes a folder from the database

    Args:
        folder_path (str): The absolute or relative path to the folder to be deleted.

    Returns:
        None: Deletes the folder from the database and returns nothing.
    """
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
