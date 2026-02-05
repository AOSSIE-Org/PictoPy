"""
One-time migration script to add Memories feature columns.
Run this ONCE after pulling the new code.

This script adds:
- latitude (REAL) column
- longitude (REAL) column
- captured_at (DATETIME) column
- Performance indexes for these columns

Usage:
    cd backend
    python migrate_add_memories_columns.py
"""

import sqlite3
from pathlib import Path
import sys


# ANSI color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


DATABASE_PATH = Path(__file__).parent / "app" / "database" / "PictoPy.db"


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """Print info message"""
    print(f"  {text}")


def check_database_exists():
    """Check if database file exists"""
    if not DATABASE_PATH.exists():
        print_error(f"Database not found at: {DATABASE_PATH}")
        print_info("The database will be created when you first run the app.")
        print_info("Run this migration script AFTER the database is created.")
        return False

    print_success(f"Database found at: {DATABASE_PATH}")
    return True


def check_images_table(cursor):
    """Check if images table exists"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='images'"
    )
    if not cursor.fetchone():
        print_error("Table 'images' does not exist")
        print_info("Run the app first to create the database schema.")
        return False

    print_success("Table 'images' exists")
    return True


def get_existing_columns(cursor):
    """Get list of existing columns in images table"""
    cursor.execute("PRAGMA table_info(images)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    return columns


def add_columns(cursor):
    """Add new columns if they don't exist"""
    print_header("Adding Memories Feature Columns")

    columns = get_existing_columns(cursor)
    changes_made = False

    # Add latitude column
    if "latitude" not in columns:
        print_info("Adding column: latitude (REAL)")
        cursor.execute("ALTER TABLE images ADD COLUMN latitude REAL")
        print_success("Column 'latitude' added")
        changes_made = True
    else:
        print_success(f"Column 'latitude' already exists ({columns['latitude']})")

    # Add longitude column
    if "longitude" not in columns:
        print_info("Adding column: longitude (REAL)")
        cursor.execute("ALTER TABLE images ADD COLUMN longitude REAL")
        print_success("Column 'longitude' added")
        changes_made = True
    else:
        print_success(f"Column 'longitude' already exists ({columns['longitude']})")

    # Add captured_at column
    if "captured_at" not in columns:
        print_info("Adding column: captured_at (DATETIME)")
        cursor.execute("ALTER TABLE images ADD COLUMN captured_at DATETIME")
        print_success("Column 'captured_at' added")
        changes_made = True
    else:
        print_success(f"Column 'captured_at' already exists ({columns['captured_at']})")

    return changes_made


def create_indexes(cursor):
    """Create indexes for performance"""
    print_header("Creating Performance Indexes")

    indexes = [
        (
            "ix_images_latitude",
            "CREATE INDEX IF NOT EXISTS ix_images_latitude ON images(latitude)",
        ),
        (
            "ix_images_longitude",
            "CREATE INDEX IF NOT EXISTS ix_images_longitude ON images(longitude)",
        ),
        (
            "ix_images_captured_at",
            "CREATE INDEX IF NOT EXISTS ix_images_captured_at ON images(captured_at)",
        ),
        (
            "ix_images_favourite_captured_at",
            "CREATE INDEX IF NOT EXISTS ix_images_favourite_captured_at ON images(isFavourite, captured_at)",
        ),
    ]

    for index_name, sql in indexes:
        cursor.execute(sql)
        print_success(f"Index '{index_name}' created")


def show_final_schema(cursor):
    """Display final table schema"""
    print_header("Final 'images' Table Schema")

    cursor.execute("PRAGMA table_info(images)")
    print(f"\n{Colors.BOLD}Columns:{Colors.RESET}")
    for row in cursor.fetchall():
        col_id, col_name, col_type, not_null, default, pk = row
        nullable = "NOT NULL" if not_null else "NULL"
        primary = " PRIMARY KEY" if pk else ""
        print(f"  {col_name:<20} {col_type:<15} {nullable:<10}{primary}")

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='images'"
    )
    indexes = cursor.fetchall()
    print(f"\n{Colors.BOLD}Indexes:{Colors.RESET}")
    for index in indexes:
        print(f"  - {index[0]}")
    print()


def migrate():
    """Run the migration"""
    print_header("PictoPy Memories Feature - Database Migration")

    # Check database exists
    if not check_database_exists():
        sys.exit(1)

    conn = None
    try:
        # Connect to database
        print_info("Connecting to database...")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print_success("Connected successfully")

        # Check images table exists
        if not check_images_table(cursor):
            sys.exit(1)

        # Add columns
        changes_made = add_columns(cursor)

        # Create indexes
        create_indexes(cursor)

        # Commit changes
        conn.commit()

        # Show final schema
        show_final_schema(cursor)

        # Summary
        print_header("Migration Summary")
        if changes_made:
            print(
                f"{Colors.BOLD}{Colors.GREEN}✅ Migration completed successfully!{Colors.RESET}\n"
            )
            print_info("New columns added to 'images' table:")
            print_info("  - latitude (REAL)")
            print_info("  - longitude (REAL)")
            print_info("  - captured_at (DATETIME)")
            print_info("")
            print_info("Performance indexes created for fast queries.")
        else:
            print(
                f"{Colors.BOLD}{Colors.GREEN}✅ Database is already up to date!{Colors.RESET}\n"
            )
            print_info("All required columns and indexes already exist.")

        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print_info(
            "1. Run metadata extraction: python -m app.utils.extract_location_metadata"
        )
        print_info("2. Verify setup: python -m app.utils.verify_memories_setup")
        print_info("3. Start the backend: ./run.sh")
        print()

    except sqlite3.Error as e:
        print_error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            print_info("Database connection closed")


if __name__ == "__main__":
    migrate()
