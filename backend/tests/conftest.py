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
    os.environ["TEST_MODE"] = "true"

    db_create_YOLO_classes_table()
    db_create_clusters_table()
    db_create_faces_table()
    db_create_folders_table()
    db_create_albums_table()
    db_create_album_images_table()
    db_create_images_table()
    db_create_metadata_table()

    yield

    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]