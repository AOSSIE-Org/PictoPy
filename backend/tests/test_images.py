"""
Comprehensive tests for the images API endpoint with pagination support.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import tempfile
import os
import sqlite3
import importlib

from app.routes.images import router as images_router


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    db_fd, db_path = tempfile.mkstemp()

    import app.config.settings
    import app.database.images
    import app.database.folders  
    import app.database.yolo_mapping

    original_db_path = app.config.settings.DATABASE_PATH
    app.config.settings.DATABASE_PATH = db_path
    
    # Reload modules to pick up new DATABASE_PATH
    importlib.reload(app.database.yolo_mapping)
    importlib.reload(app.database.folders)
    importlib.reload(app.database.images)
    
    from app.database.images import (
        db_create_images_table,
        db_bulk_insert_images,
        db_insert_image_classes_batch,
    )
    from app.database.folders import db_create_folders_table
    from app.database.yolo_mapping import db_create_YOLO_classes_table

    # Create tables in correct order (respecting foreign key dependencies)
    db_create_YOLO_classes_table()  # Creates 'mappings' table
    db_create_folders_table()
    db_create_images_table()  # Depends on folders and mappings
    
    # Verify tables were created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables created in test DB: {tables}")
    conn.close()

    # Store functions in the fixture return value so tests can use them
    yield {
        "path": db_path,
        "db_bulk_insert_images": db_bulk_insert_images,
        "db_insert_image_classes_batch": db_insert_image_classes_batch,
    }

    app.config.settings.DATABASE_PATH = original_db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    app = FastAPI()
    app.include_router(images_router, prefix="/images")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_images_data(test_db):
    """Create sample images in the test database."""
    db_path = test_db["path"]
    db_bulk_insert_images = test_db["db_bulk_insert_images"]
    db_insert_image_classes_batch = test_db["db_insert_image_classes_batch"]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    folder_id = "test-folder-id"
    cursor.execute(
        "INSERT OR IGNORE INTO folders (folder_id, folder_path, AI_Tagging) VALUES (?, ?, ?)",
        (folder_id, "/test/folder", 0)
    )
    conn.commit()

    images = []
    for i in range(100):
        images.append({
            "id": f"img_{i:03d}",
            "path": f"/test/folder/image_{i:03d}.jpg",
            "folder_id": folder_id,
            "thumbnailPath": f"/test/folder/thumb_{i:03d}.jpg",
            "metadata": '{"name": "test.jpg", "date_created": "2024-01-01", "width": 1920, "height": 1080, "file_size": 1024, "item_type": "image", "file_location": "/test"}',
            "isTagged": i % 3 == 0,
        })

    db_bulk_insert_images(images)

    cursor.execute("INSERT OR IGNORE INTO mappings (class_id, name) VALUES (?, ?)", (1, "person"))
    cursor.execute("INSERT OR IGNORE INTO mappings (class_id, name) VALUES (?, ?)", (2, "car"))
    conn.commit()
    
    image_class_pairs = []
    for i in range(0, 100, 3):
        image_class_pairs.append((f"img_{i:03d}", 1))
        if i % 6 == 0:
            image_class_pairs.append((f"img_{i:03d}", 2))

    db_insert_image_classes_batch(image_class_pairs)
    conn.close()

    return {"folder_id": folder_id, "total_images": 100}


class TestGetAllImages:
    """Test suite for GET /images endpoint."""

    def test_get_all_images_without_pagination(self, client, sample_images_data):
        response = client.get("/images/")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert data["total"] == 100
        assert len(data["data"]) == 100
        assert data["limit"] is None
        assert data["offset"] is None

    def test_get_images_with_limit(self, client, sample_images_data):
        response = client.get("/images/?limit=20")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 20
        assert data["total"] == 100
        assert data["limit"] == 20
        assert data["offset"] is None

    def test_get_images_with_limit_and_offset(self, client, sample_images_data):
        response = client.get("/images/?limit=25&offset=50")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 25
        assert data["total"] == 100
        assert data["limit"] == 25
        assert data["offset"] == 50

    def test_pagination_consistency(self, client, sample_images_data):
        page1 = client.get("/images/?limit=30&offset=0").json()
        page2 = client.get("/images/?limit=30&offset=30").json()
        page3 = client.get("/images/?limit=30&offset=60").json()

        ids_page1 = {img["id"] for img in page1["data"]}
        ids_page2 = {img["id"] for img in page2["data"]}
        ids_page3 = {img["id"] for img in page3["data"]}

        assert len(ids_page1 & ids_page2) == 0
        assert len(ids_page2 & ids_page3) == 0
        assert len(ids_page1 & ids_page3) == 0

    def test_offset_beyond_total(self, client, sample_images_data):
        """Test that offset beyond total returns empty results."""
        response = client.get("/images/?limit=20&offset=200")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 0
        assert data["total"] == 100

    def test_partial_last_page(self, client, sample_images_data):
        """Test fetching last page with partial results."""
        response = client.get("/images/?limit=30&offset=90")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 10  # Only 10 images left
        assert data["total"] == 100

    def test_filter_by_tagged_true(self, client, sample_images_data):
        """Test filtering only tagged images."""
        response = client.get("/images/?tagged=true")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # Every 3rd image is tagged: 0, 3, 6, ..., 99 = 34 images
        expected_tagged = len([i for i in range(100) if i % 3 == 0])
        assert data["total"] == expected_tagged
        assert len(data["data"]) == expected_tagged

        # Verify all returned images are tagged
        for img in data["data"]:
            assert img["isTagged"] is True

    def test_filter_by_tagged_false(self, client, sample_images_data):
        """Test filtering only untagged images."""
        response = client.get("/images/?tagged=false")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        expected_untagged = len([i for i in range(100) if i % 3 != 0])
        assert data["total"] == expected_untagged
        assert len(data["data"]) == expected_untagged

        # Verify all returned images are not tagged
        for img in data["data"]:
            assert img["isTagged"] is False

    def test_pagination_with_tagged_filter(self, client, sample_images_data):
        """Test pagination works correctly with tagged filter."""
        response = client.get("/images/?tagged=true&limit=10&offset=10")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 10
        assert data["limit"] == 10
        assert data["offset"] == 10

        # Verify all returned images are tagged
        for img in data["data"]:
            assert img["isTagged"] is True

    def test_images_have_tags(self, client, sample_images_data):
        """Test that tagged images include their tags."""
        response = client.get("/images/?tagged=true&limit=5")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        for img in data["data"]:
            assert "tags" in img
            assert img["tags"] is not None
            assert len(img["tags"]) > 0
            assert "person" in img["tags"]

    def test_images_sorted_by_path(self, client, sample_images_data):
        """Test that images are sorted by path."""
        response = client.get("/images/?limit=50")

        assert response.status_code == 200
        data = response.json()

        paths = [img["path"] for img in data["data"]]
        assert paths == sorted(paths), "Images should be sorted by path"

    def test_invalid_limit_zero(self, client, sample_images_data):
        """Test that limit=0 returns validation error."""
        response = client.get("/images/?limit=0")

        assert response.status_code == 422  # Validation error

    def test_invalid_limit_negative(self, client, sample_images_data):
        """Test that negative limit returns validation error."""
        response = client.get("/images/?limit=-10")

        assert response.status_code == 422  # Validation error

    def test_invalid_offset_negative(self, client, sample_images_data):
        """Test that negative offset returns validation error."""
        response = client.get("/images/?offset=-5")

        assert response.status_code == 422  # Validation error

    def test_limit_exceeds_maximum(self, client, sample_images_data):
        """Test that limit exceeding maximum (1000) returns validation error."""
        response = client.get("/images/?limit=1001")

        assert response.status_code == 422  # Validation error

    def test_very_large_offset(self, client, sample_images_data):
        """Test that extremely large offset is rejected."""
        response = client.get("/images/?limit=10&offset=9999999")

        assert response.status_code == 400  # Bad request

    def test_empty_database(self, client, test_db):
        """Test fetching images from empty database."""
        response = client.get("/images/")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["total"] == 0
        assert len(data["data"]) == 0

    def test_response_structure(self, client, sample_images_data):
        """Test that response has correct structure."""
        response = client.get("/images/?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Check image structure
        if len(data["data"]) > 0:
            img = data["data"][0]
            assert "id" in img
            assert "path" in img
            assert "folder_id" in img
            assert "thumbnailPath" in img
            assert "metadata" in img
            assert "isTagged" in img
            assert "tags" in img

            # Check metadata structure
            metadata = img["metadata"]
            assert "name" in metadata
            assert "width" in metadata
            assert "height" in metadata
            assert "file_size" in metadata
            assert "item_type" in metadata

    def test_single_image_dataset(self, client, test_db):
        """Test pagination with only one image."""
        db_path = test_db["path"]
        db_bulk_insert_images = test_db["db_bulk_insert_images"]
        
        # Use test_db path instead of global DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        folder_id = "single-test-folder"
        cursor.execute(
            "INSERT INTO folders (folder_id, folder_path, AI_Tagging) VALUES (?, ?, ?)",
            (folder_id, "/test", 0)
        )
        conn.commit()
        conn.close()
        
        db_bulk_insert_images([{
            "id": "single_img",
            "path": "/test/single.jpg",
            "folder_id": folder_id,
            "thumbnailPath": "/test/thumb.jpg",
            "metadata": '{"name": "single.jpg", "date_created": "2024-01-01", "width": 1920, "height": 1080, "file_size": 1024, "item_type": "image", "file_location": "/test"}',
            "isTagged": False,
        }])

        response = client.get("/images/?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["total"] == 1
        assert len(data["data"]) == 1

    def test_exact_page_boundary(self, client, sample_images_data):
        """Test when total is exactly divisible by limit."""
        # We have 100 images, fetch with limit=50 twice
        page1 = client.get("/images/?limit=50&offset=0").json()
        page2 = client.get("/images/?limit=50&offset=50").json()

        assert len(page1["data"]) == 50
        assert len(page2["data"]) == 50
        assert page1["total"] == 100
        assert page2["total"] == 100

        # Verify combined results
        all_ids = {img["id"] for img in page1["data"]} | {img["id"] for img in page2["data"]}
        assert len(all_ids) == 100
