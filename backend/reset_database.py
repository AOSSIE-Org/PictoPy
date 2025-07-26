import os
import glob


def delete_db_files():
    # Finds all .db files in the app/database directory and attempts to delete them.
    # Prints a confirmation message for each deleted file.
    # Handles PermissionError if file cannot be deleted due to access rights.
    # Catches and prints any other exceptions that occur during deletion.
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
    # If this script is run directly, execute the delete_db_files function.
    delete_db_files()
