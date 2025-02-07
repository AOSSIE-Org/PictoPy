import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import shutil
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def test_images(tmp_path_factory):
    # Create a temporary directory for test images
    test_dir = tmp_path_factory.mktemp("test_images")
    
    # Get the path to the inputs directory (relative to test file)
    inputs_dir = Path(__file__).parent / "inputs"
    
    # Copy some test images from inputs to temp directory
    test_files = [
        "000000000009.jpg",
        "000000000025.jpg",
        "000000000030.jpg"
    ]
    
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
        "paths": [str(Path(test_images) / "000000000009.jpg"),
                 str(Path(test_images) / "000000000025.jpg"),
                 str(Path(test_images) / "000000000030.jpg")]
    }
    response = client.post("/images/images", json=payload)
    assert response.status_code == 202

def test_get_all_image_objects():
    response = client.get("/images/all-image-objects")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_add_folder(test_images):
    payload = {"folder_path": test_images}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 200

def test_generate_thumbnails(test_images):
    payload = {"folder_path": test_images}
    response = client.post("/images/generate-thumbnails", json=payload)
    assert response.status_code == 201

def test_add_multiple_images_missing_paths():
    payload = {}
    response = client.post("/images/images", json=payload)
    assert response.status_code == 400

def test_delete_image_missing_path():
    payload = {}
    response = client.request("DELETE", "/images/delete-image", json=payload)
    assert response.status_code == 400

def test_delete_multiple_images_invalid_format():
    payload = {"paths": "not_a_list"}
    response = client.request("DELETE", "/images/multiple-images", json=payload)
    assert response.status_code == 400

def test_add_folder_missing_folder_path():
    payload = {}
    response = client.post("/images/add-folder", json=payload)
    assert response.status_code == 400

def test_generate_thumbnails_missing_folder_path():
    payload = {}
    response = client.request("POST", "/images/generate-thumbnails", json=payload)
    assert response.status_code == 400

def test_delete_image(test_images):
    payload = {"path": str(Path(test_images) / "000000000009.jpg")}
    response = client.request("DELETE", "/images/delete-image", json=payload)
    assert response.status_code == 200

def test_delete_multiple_images(test_images):
    payload = {
        "paths": [str(Path(test_images) / "000000000025.jpg"),
                 str(Path(test_images) / "000000000030.jpg")]
    }
    response = client.request("DELETE", "/images/multiple-images", json=payload)
    assert response.status_code == 200