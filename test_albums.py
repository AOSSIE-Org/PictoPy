import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from main import app, albums, photos
from models import SmartAlbum


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_albums():
    """Clear albums before each test."""
    albums.clear()
    yield
    albums.clear()


class TestAlbumCRUD:
    def test_list_empty_albums(self, client):
        response = client.get("/albums")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_album(self, client):
        payload = {
            "name": "Vacation Photos",
            "type": "object",
            "photos": [],
            "auto_update": False,
        }
        response = client.post("/albums", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Vacation Photos"
        assert data["type"] == "object"
        assert data["auto_update"] is False
        assert "id" in data

    def test_list_albums_after_create(self, client):
        payload = {
            "name": "Test Album",
            "type": "manual",
            "photos": [],
            "auto_update": False,
        }
        client.post("/albums", json=payload)
        response = client.get("/albums")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Album"

    def test_update_album(self, client):
        # Create an album
        create_payload = {
            "name": "Old Name",
            "type": "object",
            "photos": [],
            "auto_update": False,
        }
        create_resp = client.post("/albums", json=create_payload)
        album_id = create_resp.json()["id"]

        # Update it
        update_payload = {"name": "New Name", "auto_update": True}
        response = client.patch(f"/albums/{album_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["auto_update"] is True

    def test_update_nonexistent_album(self, client):
        payload = {"name": "Updated"}
        response = client.patch("/albums/nonexistent-id", json=payload)
        assert response.status_code == 404

    def test_delete_album(self, client):
        # Create an album
        create_payload = {
            "name": "To Delete",
            "type": "object",
            "photos": [],
            "auto_update": False,
        }
        create_resp = client.post("/albums", json=create_payload)
        album_id = create_resp.json()["id"]

        # Delete it
        response = client.delete(f"/albums/{album_id}")
        assert response.status_code == 204

        # Verify it's gone
        list_resp = client.get("/albums")
        assert len(list_resp.json()) == 0

    def test_delete_nonexistent_album(self, client):
        response = client.delete("/albums/nonexistent-id")
        assert response.status_code == 404


class TestRefresh:
    def test_refresh_object_album_cats(self, client):
        # Create a "Cats" object album
        payload = {
            "name": "Cats",
            "type": "object",
            "photos": [],
            "auto_update": False,
        }
        create_resp = client.post("/albums", json=payload)
        album_id = create_resp.json()["id"]

        # Refresh it
        response = client.post(f"/albums/{album_id}/refresh")
        assert response.status_code == 200
        data = response.json()
        # Should match p1 and p2 which have "cat" and "dog" tags
        # Only p1 has "cat" tag, so it should be included
        assert "p1" in data["photos"]

    def test_refresh_face_album(self, client):
        # Create a "Faces" face album
        payload = {
            "name": "My Faces",
            "type": "face",
            "photos": [],
            "auto_update": False,
        }
        create_resp = client.post("/albums", json=payload)
        album_id = create_resp.json()["id"]

        # Refresh it
        response = client.post(f"/albums/{album_id}/refresh")
        assert response.status_code == 200
        data = response.json()
        # Should include p3 and p4 which have faces > 0
        assert "p3" in data["photos"]
        assert "p4" in data["photos"]
        assert "p1" not in data["photos"]
        assert "p2" not in data["photos"]

    def test_refresh_manual_album(self, client):
        # Create a manual album with specific photos
        payload = {
            "name": "Manual Selection",
            "type": "manual",
            "photos": ["p1", "p2"],
            "auto_update": False,
        }
        create_resp = client.post("/albums", json=payload)
        album_id = create_resp.json()["id"]

        # Refresh it (manual albums return their existing photos)
        response = client.post(f"/albums/{album_id}/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["photos"] == ["p1", "p2"]

    def test_refresh_nonexistent_album(self, client):
        response = client.post("/albums/nonexistent-id/refresh")
        assert response.status_code == 404


class TestPhotos:
    def test_list_photos(self, client):
        response = client.get("/photos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # p1, p2, p3, p4 from sample data
        assert any(p["id"] == "p1" for p in data)

    def test_get_photo(self, client):
        response = client.get("/photos/p1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "p1"
        assert data["url"] == "http://example.com/cat.jpg"
        assert "cat" in data["tags"]

    def test_get_nonexistent_photo(self, client):
        response = client.get("/photos/nonexistent")
        assert response.status_code == 404
