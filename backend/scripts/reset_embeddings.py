import sys
import os

# Ensure backend directory is in sys.path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db_connection


def reset_embeddings():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        print("Deleting all rows from image_embeddings...")
        cursor.execute("DELETE FROM image_embeddings")
        deleted_embeddings = cursor.rowcount

        print("Setting isEmbedded=0 on all images...")
        cursor.execute("UPDATE images SET isEmbedded = 0 WHERE isEmbedded = 1")
        updated_images = cursor.rowcount

        conn.commit()

        print("Done.")
        print(f"Deleted {deleted_embeddings} embeddings.")
        print(f"Reset {updated_images} images to isEmbedded=0.")


if __name__ == "__main__":
    reset_embeddings()
