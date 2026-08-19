# Must come first: it sets TEST_MODE, which settings.py reads at import time to
# keep the suite off the user's real library database.
import tests.db_isolation  # noqa: F401

import pytest

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


@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    print("\n=== Running manual setup fixture ===")

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
        print("All database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

    yield  # This is where the tests run

    # Teardown code runs after all tests
    print("\n=== Running cleanup after all tests ===")

    # TEST_MODE stays set: unsetting it would let any late import of settings.py
    # resolve DATABASE_PATH back to the real library.
