#!/usr/bin/env python3
"""
Database migration script to add soft delete functionality.
Run this script to add the necessary columns and tables for soft delete.
"""

import sqlite3
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def migrate_database_for_soft_delete():
    """Add soft delete functionality to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Add soft delete fields to images table
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]

        if "is_deleted" not in columns:
            logger.info("Adding is_deleted column to images table")
            cursor.execute("ALTER TABLE images ADD COLUMN is_deleted BOOLEAN DEFAULT 0")

        if "deleted_at" not in columns:
            logger.info("Adding deleted_at column to images table")
            cursor.execute("ALTER TABLE images ADD COLUMN deleted_at DATETIME")

        # Create action_history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS action_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """
        )

        # Create index on action_history for performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_action_history_timestamp
            ON action_history(timestamp DESC)
        """
        )

        # Create index on images for soft delete queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_images_is_deleted
            ON images(is_deleted)
        """
        )

        conn.commit()
        logger.info("Database migration for soft delete completed successfully")

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database_for_soft_delete()
