import sqlite3
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger
from app.utils.YOLO import class_names

logger = get_logger(__name__)


def db_create_YOLO_classes_table():
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
    except sqlite3.Error as e:
        if conn is not None:
            conn.rollback()
        logger.error(f"Error creating YOLO classes table: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()
