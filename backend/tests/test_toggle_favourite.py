from fastapi.testclient import TestClient
from main import app
import pytest
import sqlite3
from app.config.settings import DATABASE_PATH

client = TestClient(app)

@pytest.fixture
def dummy_image():
    # Setup
    image_id = "test-image-123"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Metadata is empty string here to test the crash
    cursor.execute(
        "INSERT OR REPLACE INTO images (id, path, thumbnailPath, isFavourite, metadata) VALUES (?, ?, ?, ?, ?)",
        (image_id, "/tmp/test.jpg", "/tmp/thumb.jpg", 0, "")
    )
    conn.commit()
    conn.close()
    
    yield image_id
    
    # Teardown: Clean up the dummy image after tests
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
    conn.commit()
    conn.close()

def test_get_all_images_crash(dummy_image):
    """
    Test that /images/ doesn't crash if metadata is empty and returns defaults.
    """
    response = client.get("/images/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify metadata defaults are present in our dummy image
    dummy_img_data = next((img for img in data["data"] if img["id"] == dummy_image), None)
    assert dummy_img_data is not None
    
    metadata = dummy_img_data["metadata"]
    assert metadata["name"] == "Unknown"
    assert metadata["width"] == 0
    assert metadata["height"] == 0
    assert metadata["file_location"] == "Unknown"
    assert metadata["item_type"] == "unknown"

def test_toggle_favourite_non_existent_image():
    """
    Test that toggling a non-existent image returns 404, not 500.
    This relates to issue #1179.
    """
    response = client.post(
        "/images/toggle-favourite",
        json={"image_id": "non-existent-id"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"]["success"] is False
    assert response.json()["detail"]["error"] == "Image Not Found"
    assert response.json()["detail"]["message"] == "Image not found or failed to toggle"

def test_toggle_favourite_success(dummy_image):
    """
    Test that toggling an existing image works correctly.
    """
    # First toggle: 0 -> 1
    response = client.post(
        "/images/toggle-favourite",
        json={"image_id": dummy_image}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["isFavourite"] is True
    
    # Second toggle: 1 -> 0
    response = client.post(
        "/images/toggle-favourite",
        json={"image_id": dummy_image}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["isFavourite"] is False
