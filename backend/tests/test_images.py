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
    # Initialize required database tables and services before running tests
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
    # Create a temporary directory and copy test images from inputs directory for use in tests
    test_dir = tmp_path_factory.mktemp("test_images")

    # Locate inputs directory relative to this test file
    inputs_dir = Path(__file__).parent / "inputs"

    # List of test image filenames to copy
    test_files = ["000000000009.jpg", "000000000025.jpg", "000000000030.jpg"]

    # Copy each test image to the temporary test directory
    for file in test_files:
        src = inputs_dir / file
        if src.exists():
            shutil.copy(src, test_dir / file)
        else:
            raise FileNotFoundError(f"Test file {file} not found in inputs directory")

    yield str(test_dir)

    # Remove the temporary test directory and its contents after tests complete
    shutil.rmtree(test_dir)


def test_get_images(test_images):
    # Test endpoint to fetch all images; expects successful response
    response = client.get("/images/all-images")
    assert response.status_code == 200


def test_get_all_image_objects():
    # Test endpoint to fetch all image objects; expects successful response
    response = client.get("/images/all-image-objects")
    assert response.status_code == 200


def test_add_folder(test_images):
    # Test endpoint for adding a folder path containing images
    payload = {"folder_path": [test_images]}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 200


def test_generate_thumbnails(test_images):
    # Test endpoint to generate thumbnails for images in given folder paths
    payload = {"folder_paths": [test_images]}
    response = client.post("/images/generate-thumbnails", json=payload)
    assert response.status_code == 200


def test_delete_image_missing_path():
    # Test deleting image endpoint with missing 'path' parameter; expects validation error (422)
    payload = {}
    response = client.request("DELETE", "/images/delete-image", json=payload)
    assert response.status_code == 422


def test_delete_multiple_images_invalid_format():
    # Test deleting multiple images with invalid 'paths' format (not a list); expects validation error (422)
    payload = {"paths": "not_a_list"}
    response = client.request("DELETE", "/images/multiple-images", json=payload)
    assert response.status_code == 422


def test_add_folder_missing_folder_path():
    # Test adding folder endpoint without required 'folder_path' parameter; expects validation error (422)
    payload = {}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 422


def test_generate_thumbnails_missing_folder_path():
    # Test generating thumbnails endpoint without required 'folder_paths' parameter; expects validation error (422)
    payload = {}
    response = client.request("POST", "/images/generate-thumbnails", json=payload)
    assert response.status_code == 422


def test_delete_multiple_images(test_images):
    # Test deleting multiple images endpoint with valid paths; expects successful deletion (200)
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
    # Test deleting thumbnails endpoint with folder path parameter; expects validation error (422)
    params = {"folder_path": test_images}
    response = client.delete("/images/delete-thumbnails", params=params)
    assert response.status_code == 422


def test_delete_thumbnails_missing_folder_path():
    # Test deleting thumbnails endpoint without required folder path parameter; expects validation error (422)
    response = client.delete("/images/delete-thumbnails")
    assert response.status_code == 422
