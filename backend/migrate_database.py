"""
Database Migration Script
Adds the isFavourite column to existing images table if it doesn't exist.
"""

import sqlite3
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns


def migrate_database():
    """Add missing columns to the images table."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if isFavourite column exists
        if not check_column_exists(cursor, "images", "isFavourite"):
            logger.info("Adding 'isFavourite' column to images table...")
            cursor.execute(
                """
                ALTER TABLE images 
                ADD COLUMN isFavourite BOOLEAN DEFAULT 0
                """
            )
            conn.commit()
            logger.info("✓ Successfully added 'isFavourite' column")
        else:
            logger.info("✓ 'isFavourite' column already exists")

        conn.close()
        print("\n✅ Database migration completed successfully!")

    except sqlite3.Error as e:
        logger.error(f"Database migration failed: {e}")
        print(f"\n❌ Migration failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
