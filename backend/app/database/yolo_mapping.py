import sqlite3
from app.config.settings import DATABASE_PATH
from app.utils.YOLO import class_names
# i included the logger for using logger.error() as this file doesnt actually already have it imported. I have used the same convention used in faces.py
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)



def db_create_YOLO_classes_table():
    # i have removed the os lbrary and the print statement as requested by the officials
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS mappings (
                class_id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL
        )
        """
        )
        for class_id, name in enumerate(class_names):
            # Upsert, not INSERT OR REPLACE: a replace deletes the row first,
            # which cascades to every image_classes row once foreign keys are
            # on. Writing only on a real change also keeps startup from
            # marking every tagged image for metadata export.
            cursor.execute(
                "INSERT INTO mappings (class_id, name) VALUES (?, ?) "
                "ON CONFLICT(class_id) DO UPDATE SET name = excluded.name "
                "WHERE mappings.name IS NOT excluded.name",
                (
                    class_id,
                    name,
                ),  # Keep class_id as integer to match image_classes.class_id
            )

        conn.commit()
    except sqlite3.Error as v:
        logger.error(f"error updating YOLO classes table:  {v}")
    finally:
        if conn is not None:
            conn.close()
