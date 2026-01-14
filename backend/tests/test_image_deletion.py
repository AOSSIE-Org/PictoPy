import os
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path to allow imports and find main.py
sys.path.append(str(Path(__file__).parent.parent))

from main import app
from app.database.images import db_get_image_by_id, db_is_image_deleted, db_bulk_insert_images, db_create_images_table
from app.config.settings import DATABASE_PATH
import sqlite3
import uuid
import json

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Make sure images table (and deleted_images) is created
    db_create_images_table()
    
    # Use config-defined DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Ensure folders table exists (might already be created by conftest)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            folder_id TEXT PRIMARY KEY,
            folder_path TEXT UNIQUE
        )
    """)
    # Insert a fake folder for FK constraints
    cursor.execute("INSERT OR IGNORE INTO folders (folder_id, folder_path) VALUES ('1', '/fake/path')")
    conn.commit()
    conn.close()

@pytest.fixture
def mock_image(tmp_path):
    # Setup: Create a fake image file and a fake thumbnail
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    img_path = img_dir / "test_image.jpg"
    img_path.write_bytes(b"fake image data")
    
    thumb_dir = tmp_path / "thumbnails"
    thumb_dir.mkdir()
    thumb_path = thumb_dir / "test_thumb.jpg"
    thumb_path.write_bytes(b"fake thumb data")
    
    image_id = str(uuid.uuid4())
    image_record = {
        "id": image_id,
        "path": str(img_path),
        "folder_id": 1, 
        "thumbnailPath": str(thumb_path),
        "metadata": json.dumps({
            "name": "test_image.jpg",
            "width": 100,
            "height": 100,
            "file_size": 100,
            "file_location": str(img_path),
            "item_type": "image/jpeg"
        }),
        "isTagged": False
    }
    
    # Insert into DB
    db_bulk_insert_images([image_record])
    
    return image_record

def test_delete_image_success(mock_image):
    image_id = mock_image["id"]
    img_path = mock_image["path"]
    thumb_path = mock_image["thumbnailPath"]
    
    # 1. Verify existence before deletion
    assert os.path.exists(img_path)
    assert os.path.exists(thumb_path)
    assert db_get_image_by_id(image_id) is not None
    
    # 2. Call DELETE API
    response = client.delete(f"/images/{image_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 3. Verify deletion
    assert not os.path.exists(img_path)
    assert not os.path.exists(thumb_path)
    assert db_get_image_by_id(image_id) is None
    assert db_is_image_deleted(img_path) is True

def test_delete_image_not_found():
    response = client.delete("/images/non-existent-id")
    assert response.status_code == 404

def test_tombstone_prevents_indexing(mock_image):
    image_id = mock_image["id"]
    img_path = mock_image["path"]
    
    # Delete the image first
    client.delete(f"/images/{image_id}")
    assert db_is_image_deleted(img_path) is True
    
    # Re-create the file manually
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    with open(img_path, "wb") as f:
        f.write(b"recreated file")
    
    # Try to re-index it via utilities
    from app.utils.images import image_util_prepare_image_records
    
    # Mocking folder_path_to_id
    folder_path = str(Path(img_path).parent)
    records = image_util_prepare_image_records([str(img_path)], {folder_path: 1})
    
    # It should skip it because of the tombstone
    assert len(records) == 0
