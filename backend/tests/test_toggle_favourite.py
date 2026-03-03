from fastapi.testclient import TestClient
from main import app
import pytest
import sqlite3
from app.config.settings import DATABASE_PATH

client = TestClient(app)

@pytest.fixture
def dummy_image():
    # Insert a dummy image into the database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    image_id = "test-image-123"
    # Metadata is empty string here to test the crash
    cursor.execute(
        "INSERT OR REPLACE INTO images (id, path, thumbnailPath, isFavourite, metadata) VALUES (?, ?, ?, ?, ?)",
        (image_id, "/tmp/test.jpg", "/tmp/thumb.jpg", 0, "")
    )
    conn.commit()
    conn.close()
    return image_id

def test_get_all_images_crash(dummy_image):
    """
    Test that /images/ doesn't crash if metadata is empty.
    """
    response = client.get("/images/")
    assert response.status_code == 200
    assert response.json()["success"] is True

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
