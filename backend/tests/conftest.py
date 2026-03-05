import pytest
import os
import tempfile
import sqlite3

# Import database table creation functions
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table, db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table

@pytest.fixture
def temp_db_path(monkeypatch):
    """
    Creates a temporary SQLite database file
    and patches DATABASE_PATH in all database modules.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    db_path = temp_file.name

    # Patch DATABASE_PATH in ALL database modules
    modules_to_patch = [
        "app.database.connection",
        "app.database.faces",
        "app.database.images",
        "app.database.face_clusters",
        "app.database.yolo_mapping",
        "app.database.albums",
        "app.database.folders",
        "app.database.metadata",
    ]

    for module in modules_to_patch:
        monkeypatch.setattr(f"{module}.DATABASE_PATH", db_path, raising=False)

    yield db_path

    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

 