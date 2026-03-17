import json
import logging
import sqlite3
from typing import Any, Dict, Optional

from app.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)


def db_create_metadata_table() -> None:
    """Create the metadata table if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                metadata TEXT
            )
        """
        )

        # Insert initial row if table is empty
        cursor.execute("SELECT COUNT(*) FROM metadata")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO metadata (metadata) VALUES (?)", ("{}",))

        conn.commit()
    except sqlite3.Error:
        if conn is not None:
            conn.rollback()
        logger.exception("Failed to create metadata table")
        raise
    finally:
        if conn is not None:
            conn.close()


def db_get_metadata() -> Optional[Dict[str, Any]]:
    """
    Get the metadata from the database.

    Returns:
        Dictionary containing metadata, or None if not found
    """
    conn = None

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT metadata FROM metadata LIMIT 1")

        row = cursor.fetchone()

        if row and row[0]:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                logger.exception("Failed to decode metadata JSON")
                return None
        return None
    except sqlite3.Error:
        logger.exception("Failed to fetch metadata")
        return None
    finally:
        if conn is not None:
            conn.close()


def db_update_metadata(
    metadata: Dict[str, Any], cursor: Optional[sqlite3.Cursor] = None
) -> bool:
    """
    Update the metadata in the database.

    Args:
        metadata: Dictionary containing metadata to store
        cursor: Optional existing database cursor. If None, creates a new connection.

    Returns:
        True if the metadata was updated, False otherwise
    """
    conn: Optional[sqlite3.Connection] = None
    own_connection = cursor is None
    if own_connection:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

    try:
        metadata_json = json.dumps(metadata)

        # Delete all existing rows and insert new one
        cursor.execute("DELETE FROM metadata")
        cursor.execute("INSERT INTO metadata (metadata) VALUES (?)", (metadata_json,))

        success = cursor.rowcount > 0
        if own_connection:
            conn.commit()
        return success
    except sqlite3.Error:
        if own_connection and conn is not None:
            conn.rollback()
        logger.exception("Failed to update metadata")
        raise
    finally:
        if own_connection and conn is not None:
            conn.close()
