from main import app
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import shutil
import os
from app.database.images import create_image_id_mapping_table, create_images_table
from app.database.albums import create_albums_table
from app.database.yolo_mapping import create_YOLO_mappings
from app.database.faces import cleanup_face_embeddings, create_faces_table
from app.facecluster.init_face_cluster import init_face_cluster
from app.database.folders import create_folders_table

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def initialize_database_and_services():
    # Run your initialization functions before any tests are executed
    create_YOLO_mappings()
    create_faces_table()
    create_image_id_mapping_table()
    create_images_table()
    create_folders_table()
    create_albums_table()
    cleanup_face_embeddings()
    init_face_cluster()
    yield


@pytest.fixture(scope="module")
def test_images(tmp_path_factory):
    # Create a temporary directory for test images
    test_dir = tmp_path_factory.mktemp("test_images")

    # Get the path to the inputs directory (relative to test file)
    inputs_dir = Path(__file__).parent / "inputs"

    # Copy some test images from inputs to temp directory
    test_files = ["000000000009.jpg", "000000000025.jpg", "000000000030.jpg"]

    for file in test_files:
        src = inputs_dir / file
        if src.exists():
            shutil.copy(src, test_dir / file)
        else:
            raise FileNotFoundError(f"Test file {file} not found in inputs directory")

    yield str(test_dir)

    # Cleanup after tests
    shutil.rmtree(test_dir)


def test_get_images(test_images):
    response = client.get("/images/all-images")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_multiple_images(test_images):
    payload = {
        "paths": [
            str(Path(test_images) / "000000000009.jpg"),
            str(Path(test_images) / "000000000025.jpg"),
            str(Path(test_images) / "000000000030.jpg"),
        ]
    }

    print("Payload = ", payload)

    response = client.post("/images/images", json=payload)
    assert response.status_code == 202


def test_get_all_image_objects():
    response = client.get("/images/all-image-objects")
    assert response.status_code == 200


def test_add_folder(test_images):
    payload = {"folder_path": [test_images]}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 200


def test_generate_thumbnails(test_images):
    payload = {"folder_paths": [test_images]}
    response = client.post("/images/generate-thumbnails", json=payload)
    assert response.status_code == 200


def test_add_multiple_images_missing_paths():
    payload = {}
    response = client.post("/images/images", json=payload)
    assert response.status_code == 422


def test_delete_image_missing_path():
    payload = {}
    response = client.request("DELETE", "/images/delete-image", json=payload)
    assert response.status_code == 422


def test_delete_multiple_images_invalid_format():
    payload = {"paths": "not_a_list"}
    response = client.request("DELETE", "/images/multiple-images", json=payload)
    assert response.status_code == 422


def test_add_folder_missing_folder_path():
    payload = {}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 422


def test_generate_thumbnails_missing_folder_path():
    payload = {}
    response = client.request("POST", "/images/generate-thumbnails", json=payload)
    assert response.status_code == 422


def test_delete_multiple_images(test_images):
    payload = {
        "paths": [
            str(Path(test_images) / "000000000025.jpg"),
            str(Path(test_images) / "000000000030.jpg"),
        ],
        "isFromDevice": False,
    }
    response = client.request("DELETE", "/images/multiple-images", json=payload)
    assert response.status_code == 200


def test_delete_thumbnails(test_images):
    params = {"folder_path": test_images}
    response = client.delete("/images/delete-thumbnails", params=params)
    assert response.status_code == 422


def test_delete_thumbnails_missing_folder_path():
    response = client.delete("/images/delete-thumbnails")
    assert response.status_code == 422
