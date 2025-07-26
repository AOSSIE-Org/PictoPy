import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import sys
import os
from pathlib import Path
import shutil
from app.utils.metadata import extract_metadata
from app.database.images import (
    insert_image_db,
)
from app.database.images import create_image_id_mapping_table, create_images_table
from app.database.albums import create_albums_table
from app.database.yolo_mapping import create_YOLO_mappings
from app.database.faces import cleanup_face_embeddings, create_faces_table
from app.facecluster.init_face_cluster import init_face_cluster

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def initialize_database_and_services():
    # Initialize all required database tables and services before running tests
    create_YOLO_mappings()
    create_faces_table()
    create_image_id_mapping_table()
    create_images_table()
    create_albums_table()
    cleanup_face_embeddings()
    init_face_cluster()
    yield


@pytest.fixture(scope="module")
def test_images(tmp_path_factory):
    # Prepare a temporary directory with test images copied from inputs directory
    test_dir = tmp_path_factory.mktemp("test_images")

    # Locate the inputs directory relative to the test file
    inputs_dir = Path(__file__).parent / "inputs"

    # List of test image files to copy
    test_files = [
        "000000000009.jpg",
    ]

    # Copy each test file into the temporary test directory
    for file in test_files:
        src = inputs_dir / file
        if src.exists():
            shutil.copy(src, test_dir / file)
        else:
            raise FileNotFoundError(f"Test file {file} not found in inputs directory")

    yield str(test_dir)

    # Clean up temporary test images directory after tests finish
    shutil.rmtree(test_dir)


@pytest.fixture
def mock_album_data():
    # Provide mock data representing an album with a name and description
    return {"name": "Test Album", "description": "This is a test album"}


def test_create_new_album(mock_album_data):
    # Test album creation endpoint, mocking the underlying DB call
    with patch("app.database.albums.create_album"):
        response = client.post("/albums/create-album", json=mock_album_data)
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_add_multiple_images_to_album(test_images):
    # Test adding multiple images to an album, insert image metadata before API call
    payload = {
        "album_name": "Test Album",
        "paths": [str(Path(test_images) / "000000000009.jpg")],
    }
    with patch("app.database.albums.add_photo_to_album"):
        insert_image_db(
            str(Path(test_images) / "000000000009.jpg"),
            [],
            extract_metadata(str(Path(test_images) / "000000000009.jpg")),
        )
        response = client.request("POST", "/albums/add-multiple-to-album", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_remove_image_from_album(test_images):
    # Test removing a single image from an album and deleting multiple images via API
    payload = {
        "album_name": "Test Album",
        "path": str(Path(test_images) / "000000000009.jpg"),
    }
    with patch("app.database.albums.remove_photo_from_album"):
        response = client.request("DELETE", "/albums/remove-from-album", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Additional test for deleting multiple images
        payload2 = {
            "paths": [str(Path(test_images) / "000000000009.jpg")],
            "isFromDevice": False,
        }

        response2 = client.request("DELETE", "/images/multiple-images", json=payload2)
        assert response2.status_code == 200


def test_view_album_photos():
    # Test retrieval of photos within an album by mocking DB response
    with patch(
        "app.database.albums.get_album_photos",
        return_value=["image1.jpg", "image2.jpg"],
    ):
        response = client.get("/albums/view-album?album_name=Test Album")
        assert response.status_code == 200


def test_update_album_description():
    # Test updating album description endpoint with mocked DB call
    payload = {"album_name": "Test Album", "description": "Updated description"}
    with patch("app.database.albums.edit_album_description"):
        response = client.put("/albums/edit-album-description", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_get_albums():
    # Test retrieval of all albums by mocking the DB to return sample albums
    mock_albums = [
        {"name": "Album1", "description": "Desc1"},
        {"name": "Album2", "description": "Desc2"},
    ]
    with patch("app.database.albums.get_all_albums", return_value=mock_albums):
        response = client.get("/albums/view-all")
        assert response.status_code == 200


def test_delete_existing_album():
    # Test deleting an album with mocked DB delete_album function
    with patch("app.database.albums.delete_album"):
        response = client.request(
            "DELETE", "/albums/delete-album", json={"name": "Test Album"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
