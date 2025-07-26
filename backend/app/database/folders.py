import sqlite3
import os
from app.config.settings import DATABASE_PATH


def create_folders_table():
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
# Creates the 'folders' table to store folder paths and their last modification times.
# folder_path is unique and folder_id is the primary key.


def insert_folder(folder_path):
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
# Inserts a new folder record if it doesn't exist.
# Returns the folder_id of the inserted or existing folder.
# Raises an error if the folder path is not a valid directory.


def get_folder_id_from_path(folder_path):
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
# Retrieves the folder_id given an absolute folder path.
# Returns None if folder does not exist in the database.


def get_folder_path_from_id(folder_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT folder_path FROM folders WHERE folder_id = ?",
        (folder_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
# Retrieves the folder path given a folder_id.
# Returns None if no folder with that ID exists.


def get_all_folders():
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute("SELECT folder_path FROM folders").fetchall()
        return [row[0] for row in rows] if rows else []
# Returns a list of all folder paths stored in the database.
# Returns an empty list if no folders are found.


def get_all_folder_ids():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id from folders")
    rows = cursor.fetchall()
    return [row[0] for row in rows] if rows else []
# Returns a list of all folder IDs stored in the database.
# Returns an empty list if no folder IDs are found.


def delete_folder(folder_path):
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
# Deletes a folder record from the database by its folder path.
# Enforces foreign key constraints to cascade delete related records.
# Raises an error if the folder does not exist in the database.
