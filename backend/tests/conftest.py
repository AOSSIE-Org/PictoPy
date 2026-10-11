# ruff: noqa: E402 -- app imports must follow the database guard below.
import pytest
import os

# settings.py picks the database once, at import, and only this flag points it
# away from the user's live library. Set before any app import so a local run
# can never migrate or write to it.
os.environ["GITHUB_ACTIONS"] = "true"

from app.config import settings

# If anything imported settings before this file, the flag came too late.
assert (
    os.path.basename(settings.DATABASE_PATH) == "test_db.sqlite3"
), f"refusing to run tests against {settings.DATABASE_PATH}"

# Import database table creation functions
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.videos import db_create_videos_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table, db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table
from app.database.semantic_labels import db_create_semantic_labels_table
from app.database.image_embeddings import db_create_image_embeddings_table
from app.database.video_frames import db_create_video_frames_tables
from app.database.memories import db_create_memories_table
from app.database.xmp_export_state import db_create_image_xmp_state_table


@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    print("\n=== Running manual setup fixture ===")

    # Set test environment
    os.environ["TEST_MODE"] = "true"

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
        db_create_videos_table()
        db_create_semantic_labels_table()
        db_create_image_embeddings_table()
        db_create_video_frames_tables()
        db_create_metadata_table()
        db_create_memories_table()  # References images(id) and videos(id)
        db_create_image_xmp_state_table()  # Triggers watch the tables above
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
