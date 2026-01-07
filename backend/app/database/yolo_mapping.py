from app.database.connection import get_db_transaction
from app.utils.YOLO import class_names
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def db_create_YOLO_classes_table() -> None:
    """Create the YOLO class mappings table and populate it with class names."""
    with get_db_transaction() as conn:
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
            cursor.execute(
                "INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)",
                (
                    class_id,
                    name,
                ),  # Keep class_id as integer to match image_classes.class_id
            )
