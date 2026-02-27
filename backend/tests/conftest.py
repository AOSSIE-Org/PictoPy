import pytest
import os

# Import database table creation functions
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table, db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table


@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    print("\n=== Running manual setup fixture ===")

    # Set test environment
    os.environ["TEST_MODE"] = "true"

    # Skip DB creation when running unit-only tests (e.g. test_images.py) that mock the DB.
    # Use: PICTOPY_SKIP_DB_SETUP=1 pytest tests/test_images.py
    if os.environ.get("PICTOPY_SKIP_DB_SETUP") == "1":
        print("Skipping database setup (PICTOPY_SKIP_DB_SETUP=1).")
        yield
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]
        return

    # Create all database tables in the same order as main.py
    print("Creating database tables...")
    try:
        db_create_YOLO_classes_table()
        db_create_clusters_table()  # Create clusters table first since faces references it
        db_create_faces_table()
        db_create_folders_table()
        db_create_albums_table()
        db_create_album_images_table()
        db_create_images_table()
        db_create_metadata_table()
        print("All database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

    yield  # This is where the tests run

    # Teardown code runs after all tests
    print("\n=== Running cleanup after all tests ===")

    # Cleanup code here
    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]
