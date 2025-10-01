import sqlite3
from app.config.settings import DATABASE_PATH
from app.utils.YOLO import class_names


def db_create_YOLO_classes_table():
    # print current directory:
    import os

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS mappings (
            class_id TEXT PRIMARY KEY,
            name VARCHAR NOT NULL
    )
    """
    )
    for class_id, name in enumerate(class_names):
        cursor.execute(
            "INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)",
            (str(class_id), name),  # Convert class_id to string since it's now TEXT
        )

    conn.commit()
    conn.close()
