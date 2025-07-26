import sqlite3
from app.config.settings import DATABASE_PATH
from app.yolov8.utils import class_names


def create_YOLO_mappings():
    # Creates the 'mappings' table in the database if it doesn't exist.
    # This table maps YOLO class IDs (integers) to their corresponding class names (strings).
    # If an entry already exists for a class ID, it is replaced with the new value.

    # Optional: Print current working directory (useful for debugging file paths).
    import os
    print(os.getcwd())

    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create the mappings table with class_id as the primary key
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS mappings (
            class_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
    )
    """
    )

    # Insert or update each class ID and name from the YOLO class_names list
    for class_id, name in enumerate(class_names):
        cursor.execute(
            "INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)",
            (class_id, name),
        )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
