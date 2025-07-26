import sqlite3
import os
from app.config.settings import DATABASE_PATH


def create_folders_table():
    # Creates the 'folders' table in the SQLite database if it doesn't already exist.
    # The table stores a unique folder ID, absolute folder path, and last modified time.
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


def insert_folder(folder_path):
    # Inserts a folder into the 'folders' table.
    # If the folder already exists, returns its existing ID.
    # Otherwise, inserts it and returns the new folder ID.
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

    # Get the last modified time of the folder in Unix timestamp format
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


def get_folder_id_from_path(folder_path):
    # Given a folder path, returns the corresponding folder ID from the database.
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


def get_folder_path_from_id(folder_id):
    # Given a folder ID, returns the corresponding folder path from the database.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT folder_path FROM folders WHERE folder_id = ?",
        (folder_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_all_folders():
    # Returns a list of all folder paths stored in the 'folders' table.
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute("SELECT folder_path FROM folders").fetchall()
        return [row[0] for row in rows] if rows else []


def get_all_folder_ids():
    # Returns a list of all folder IDs stored in the 'folders' table.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id from folders")
    rows = cursor.fetchall()
    return [row[0] for row in rows] if rows else []


def delete_folder(folder_path):
    # Deletes a folder entry from the 'folders' table using its path.
    # Enables foreign key constraints to cascade deletes in referencing tables.
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    abs_folder_path = os.path.abspath(folder_path)
    cursor.execute(
        "PRAGMA foreign_keys = ON;"
    )  # Required for enforcing ON DELETE CASCADE in related tables
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
