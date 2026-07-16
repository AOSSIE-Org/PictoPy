import os
import sys
from app.config.settings import DATABASE_PATH


def delete_db_files():
    # 1. Target the configured database path and its SQLite helper files
    db_files = [
        DATABASE_PATH,
        DATABASE_PATH + "-journal",
        DATABASE_PATH + "-wal",
        DATABASE_PATH + "-shm",
    ]

    # 2. Target explicitly supported test database files and their helper files
    test_db_files = [
        "test_db.sqlite3",
        "test_db.sqlite3-journal",
        "test_db.sqlite3-wal",
        "test_db.sqlite3-shm",
    ]
    db_files.extend(test_db_files)

    # Normalize paths and remove duplicates
    unique_db_files = sorted({os.path.abspath(f) for f in db_files})

    deleted_any = False
    has_errors = False
    for db_file in unique_db_files:
        if os.path.isfile(db_file):
            try:
                os.remove(db_file)
                print(f"Deleted: {db_file}")
                deleted_any = True
            except PermissionError as e:
                print(f"Permission denied: {db_file} ({e})", file=sys.stderr)
                has_errors = True
            except Exception as e:
                print(f"Error deleting {db_file}: {e}", file=sys.stderr)
                has_errors = True

    if not deleted_any and not has_errors:
        print("No database files were found or deleted.")

    if has_errors:
        print("Error: Database reset failed because some files could not be deleted.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    delete_db_files()


