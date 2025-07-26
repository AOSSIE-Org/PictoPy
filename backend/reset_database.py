import os
import glob


def delete_db_files():
    """
    Deletes all .db files located in the 'app/database/' directory.
    Handles and reports any PermissionError or other exceptions encountered during deletion.
    """
    db_files = glob.glob("app/database/*.db")
    for db_file in db_files:
        try:
            os.remove(db_file)
            print(f"Deleted: {db_file}")
        except PermissionError:
            print(f"Permission denied: {db_file}")
        except Exception as e:
            print(f"Error deleting {db_file}: {e}")


if __name__ == "__main__":
    delete_db_files()
