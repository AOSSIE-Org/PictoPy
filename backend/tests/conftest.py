import pytest
import os
import tempfile


@pytest.fixture
def temp_db_path(monkeypatch):
    """
    Creates a temporary SQLite database file
    and patches DATABASE_PATH in all database modules.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    db_path = temp_file.name

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
