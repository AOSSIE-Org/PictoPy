import os
import glob
from app.config.settings import DATABASE_PATH


def delete_db_files():
    # 1. Target the configured database path and its SQLite helper files
    db_files = [
        DATABASE_PATH,
        DATABASE_PATH + "-journal",
        DATABASE_PATH + "-wal",
        DATABASE_PATH + "-shm",
    ]

    # 2. Also search for any other database files in the same directory
    db_dir = os.path.dirname(DATABASE_PATH)
    if os.path.exists(db_dir):
        patterns = [
            os.path.join(db_dir, "*.db"),
            os.path.join(db_dir, "*.db-journal"),
            os.path.join(db_dir, "*.db-wal"),
            os.path.join(db_dir, "*.db-shm"),
            os.path.join(db_dir, "*.sqlite3"),
        ]
        for pattern in patterns:
            db_files.extend(glob.glob(pattern))

    # 3. Support local testing files in current working directory (e.g. test_db.sqlite3)
    db_files.extend(glob.glob("*.sqlite3"))
    db_files.extend(glob.glob("test_db.sqlite3*"))

    # Normalize paths and remove duplicates
    unique_db_files = sorted(list(set(os.path.abspath(f) for f in db_files)))

    deleted_any = False
    for db_file in unique_db_files:
        if os.path.isfile(db_file):
            try:
                os.remove(db_file)
                print(f"Deleted: {db_file}")
                deleted_any = True
            except PermissionError:
                print(f"Permission denied: {db_file}")
            except Exception as e:
                print(f"Error deleting {db_file}: {e}")

    if not deleted_any:
        print("No database files were found or deleted.")


if __name__ == "__main__":
    delete_db_files()

