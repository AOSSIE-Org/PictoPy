import sqlite3
import os
from app.config.settings import DATABASE_PATH
from app.database.connection_pool import get_connection, return_connection


def create_folders_table():
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
    finally:
        return_connection(conn)


def insert_folder(folder_path):
    conn = get_connection()
    cursor = conn.cursor()

    abs_folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(abs_folder_path):
        return_connection(conn)
        raise ValueError(f"Error: '{folder_path}' is not a valid directory.")

    try:
        cursor.execute(
            "SELECT folder_id FROM folders WHERE folder_path = ?",
            (abs_folder_path,),
        )
        existing_folder = cursor.fetchone()

        if existing_folder:
            return existing_folder[0]

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

        return result[0] if result else None
    finally:
        return_connection(conn)


def get_folder_id_from_path(folder_path):
    conn = get_connection()
    cursor = conn.cursor()
    abs_folder_path = os.path.abspath(folder_path)
    try:
        cursor.execute(
            "SELECT folder_id FROM folders WHERE folder_path = ?",
            (abs_folder_path,),
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        return_connection(conn)


def get_folder_path_from_id(folder_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT folder_path FROM folders WHERE folder_id = ?",
            (folder_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        return_connection(conn)


def get_all_folders():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        rows = cursor.execute("SELECT folder_path FROM folders").fetchall()
        return [row[0] for row in rows] if rows else []
    finally:
        return_connection(conn)


def get_all_folder_ids():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT folder_id from folders")
        rows = cursor.fetchall()
        return [row[0] for row in rows] if rows else []
    finally:
        return_connection(conn)


def delete_folder(folder_path):
    conn = get_connection()
    cursor = conn.cursor()
    abs_folder_path = os.path.abspath(folder_path)
    
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")  
        conn.commit()
        cursor.execute(
            "SELECT folder_id FROM folders WHERE folder_path = ?",
            (abs_folder_path,),
        )
        existing_folder = cursor.fetchone()

        if not existing_folder:
            raise ValueError(
                f"Error: Folder '{folder_path}' does not exist in the database."
            )

        cursor.execute(
            "DELETE FROM folders WHERE folder_path = ?",
            (abs_folder_path,),
        )

        conn.commit()
    finally:
        return_connection(conn)
