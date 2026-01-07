# This DB table contains metadata about the application and user preferences.
import sqlite3
import json
from typing import Optional, Dict, Any

from app.database.connection import (
    get_db_connection,
    get_db_transaction,
    get_db_write_transaction,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def db_create_metadata_table() -> None:
    """Create the metadata table if it doesn't exist."""
    with get_db_transaction() as conn:
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


def db_get_metadata() -> Optional[Dict[str, Any]]:
    """
    Get the metadata from the database.

    Returns:
        Dictionary containing metadata, or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT metadata FROM metadata LIMIT 1")

        row = cursor.fetchone()

        if row and row[0]:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None
        return None


def db_update_metadata(
    metadata: Dict[str, Any], cursor: Optional[sqlite3.Cursor] = None
) -> bool:
    """
    Update the metadata in the database.

    Args:
        metadata: Dictionary containing metadata to store
        cursor: Optional existing database cursor (deprecated, kept for compatibility)

    Returns:
        True if the metadata was updated, False otherwise
    """
    metadata_json = json.dumps(metadata)

    if cursor is not None:
        # Use provided cursor (external transaction management)
        cursor.execute("DELETE FROM metadata")
        cursor.execute("INSERT INTO metadata (metadata) VALUES (?)", (metadata_json,))
        return cursor.rowcount > 0
    else:
        # Use our own transaction
        with get_db_write_transaction() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM metadata")
            cur.execute("INSERT INTO metadata (metadata) VALUES (?)", (metadata_json,))
            return cur.rowcount > 0
