import sqlite3
from app.yolov8.utils import class_names

def create_YOLO_mappings():
    conn = sqlite3.connect("mappings.db")
    cursor = conn.cursor()

    cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mappings (
            class_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
    )
    """
    )
    for class_id, name in enumerate(class_names):
        cursor.execute("INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)", (class_id, name))
    
    conn.commit()
    conn.close()
