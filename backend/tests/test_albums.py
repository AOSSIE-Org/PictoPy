import sys
import os
import pytest
import bcrypt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid
from app.routes import albums as albums_router

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = FastAPI()
app.include_router(albums_router.router, prefix="/albums", tags=["albums"])

client = TestClient(app)

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture
def mock_db_album():
    return {
        "album_id": str(uuid.uuid4()),
        "album_name": "Summer Vacation",
        "description": "Photos from our 2023 summer trip.",
        "cover_image_id": None,
        "is_hidden": False,
        "password_hash": None,
        "created_at": "2023-01-01 12:00:00",
        "updated_at": "2023-01-01 12:00:00"
    }


@pytest.fixture
def mock_db_hidden_album():
    return {
        "album_id": str(uuid.uuid4()),
        "album_name": "Secret Party",
        "description": "Don't tell anyone.",
        "cover_image_id": None,
        "is_hidden": True,
        "password_hash": "a_very_secure_hash",
        "created_at": "2023-01-01 12:00:00",
        "updated_at": "2023-01-01 12:00:00"
    }


# ##############################
# Test Classes
# ##############################


class TestAlbumRoutes:
    """Test suite for the main album CRUD routes."""

    @pytest.mark.parametrize(
        "album_data",
        [
            {
                "name": "New Year's Eve",
                "description": "Party photos from 2024.",
                "cover_image_id": None,
                "is_hidden": False,
                "password": None,
            },
            {
                "name": "Secret Vault",
                "description": "Hidden memories.",
                "cover_image_id": None,
                "is_hidden": True,
                "password": "supersecret",
            },
        ],
    )
    def test_create_album_variants(self, album_data):
        with patch("app.routes.albums.db_get_album_by_name") as mock_get_by_name, patch(
            "app.routes.albums.db_insert_album"
        ) as mock_insert:
            mock_get_by_name.return_value = None  # No existing album
            mock_insert.return_value = True

            response = client.post("/albums/", json=album_data)
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "album_id" in json_response

            mock_insert.assert_called_once()
            # Verify that the album_id is a valid UUID
            album_id = json_response["album_id"]
            uuid.UUID(album_id)

    def test_create_album_duplicate_name(self):
        """Test creating album with duplicate name."""
        album_data = {
            "name": "Existing Album",
            "description": "This name already exists",
            "is_hidden": False,
            "password": None,
        }

        with patch("app.routes.albums.db_get_album_by_name") as mock_get_by_name:
            # Mock must return a dict (or truthy object), not tuple
            mock_get_by_name.return_value = {"album_id": "existing"}

            response = client.post("/albums/", json=album_data)
            assert response.status_code == 409

            json_response = response.json()
            assert json_response["detail"]["success"] is False
            assert json_response["detail"]["error"] == "Album Already Exists"

    def test_get_all_albums_public_only(self, mock_db_album):
        """
        Test fetching only public albums (default behavior).
        """
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            # Return list of dicts
            mock_get_all.return_value = [mock_db_album]

            response = client.get("/albums/")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert isinstance(json_response["albums"], list)
            assert len(json_response["albums"]) == 1
            assert json_response["albums"][0]["album_id"] == mock_db_album["album_id"]
            
            mock_get_all.assert_called_once_with(False)

    def test_get_all_albums_include_hidden(self, mock_db_album, mock_db_hidden_album):
        """
        Test fetching all albums including hidden ones.
        """
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            mock_get_all.return_value = [mock_db_album, mock_db_hidden_album]

            response = client.get("/albums/?show_hidden=true")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert len(json_response["albums"]) == 2

            ids = {album["album_id"] for album in json_response["albums"]}
            assert mock_db_album["album_id"] in ids
            assert mock_db_hidden_album["album_id"] in ids

            mock_get_all.assert_called_once_with(True)

    def test_get_all_albums_empty_list(self):
        """
        Test fetching albums when none exist.
        """
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            mock_get_all.return_value = []

            response = client.get("/albums/")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert json_response["albums"] == []

    def test_get_album_by_id_success(self, mock_db_album):
        """
        Test fetching a single album by its ID successfully.
        """
        with patch("app.routes.albums.db_get_album") as mock_get_album:
            mock_get_album.return_value = mock_db_album

            response = client.get(f"/albums/{mock_db_album['album_id']}")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert json_response["data"]["album_id"] == mock_db_album["album_id"]
            assert json_response["data"]["album_name"] == mock_db_album["album_name"]
            
            mock_get_album.assert_called_once_with(mock_db_album["album_id"])

    def test_get_album_by_id_not_found(self):
        """
        Test fetching a single album that does not exist.
        """
        non_existent_id = str(uuid.uuid4())

        with patch("app.routes.albums.db_get_album") as mock_get_album:
            mock_get_album.return_value = None

            response = client.get(f"/albums/{non_existent_id}")
            assert response.status_code == 404
            json_response = response.json()

            assert json_response["detail"]["error"] == "Album Not Found"

    @pytest.mark.parametrize(
        "album_data_override, request_data, verify_password_return, expected_status",
        [
            # Case 1: Public album
            (
                {"is_hidden": False, "password_hash": None},
                {
                    "name": "Updated Public Album",
                    "description": "Updated description",
                    "cover_image_id": None,
                    "is_hidden": False,
                    "password": None,
                    "current_password": None,
                },
                True,
                200,
            ),
            # Case 2: Hidden album, correct password
            (
                {"is_hidden": True, "password_hash": "hashed_pw"},
                {
                    "name": "Updated Hidden Album",
                    "description": "Updated hidden description",
                    "cover_image_id": None,
                    "is_hidden": True,
                    "password": "newpass123",
                    "current_password": "oldpass",
                },
                True,
                200,
            ),
            # Case 3: Hidden album, wrong password
            (
                {"is_hidden": True, "password_hash": "hashed_pw"},
                {
                    "name": "Invalid Attempt",
                    "description": "Wrong password used",
                    "cover_image_id": None,
                    "is_hidden": True,
                    "password": "newpass123",
                    "current_password": "wrongpass",
                },
                False,
                401,
            ),
        ],
    )
    def test_update_album(
        self, mock_db_album, album_data_override, request_data, verify_password_return, expected_status
    ):
        # Update fixture data with parametrization overrides
        current_album_data = mock_db_album.copy()
        current_album_data.update(album_data_override)

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_update_album"
        ) as mock_update_album, patch(
            "app.routes.albums.verify_album_password"
        ) as mock_verify:
            mock_get_album.return_value = current_album_data
            mock_verify.return_value = verify_password_return

            response = client.put(f"/albums/{current_album_data['album_id']}", json=request_data)
            assert response.status_code == expected_status

            if expected_status == 200:
                assert response.json()["success"] is True
                mock_update_album.assert_called_once()
            else:
                mock_update_album.assert_not_called()

    def test_delete_album_success(self, mock_db_album):
        """
        Test successfully deleting an existing album.
        """
        album_id = mock_db_album["album_id"]
        
        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_delete_album"
        ) as mock_delete_album:
            mock_get_album.return_value = mock_db_album
            mock_delete_album.return_value = None

            response = client.delete(f"/albums/{album_id}")

            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert json_response["msg"] == "Album deleted successfully"
            mock_delete_album.assert_called_once_with(album_id)


class TestAlbumMediaManagement:
    """
    Test suite for routes managing media (images/videos) within albums.
    """

    def test_add_media_to_album_success(self, mock_db_album):
        """
        Test adding valid media items to an existing album.
        """
        album_id = mock_db_album["album_id"]
        # Updated request body format for media items
        request_body = {
            "media_items": [
                {"media_id": "img-1", "media_type": "image"},
                {"media_id": "vid-1", "media_type": "video"},
            ]
        }

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_add_media_to_album"
        ) as mock_add_media:
            mock_get_album.return_value = mock_db_album
            mock_add_media.return_value = 2

            # Updated endpoint: /media
            response = client.post(f"/albums/{album_id}/media", json=request_body)
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "msg" in json_response
            assert "Added 2 items" in json_response["msg"]

            mock_add_media.assert_called_once()

    def test_get_album_media_success(self, mock_db_album):
        """
        Test retrieving media items from an existing album.
        """
        album_id = mock_db_album["album_id"]
        expected_media = [
            {"media_id": "img-1", "media_type": "image"},
            {"media_id": "vid-1", "media_type": "video"},
        ]

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_get_album_media"
        ) as mock_get_media:
            mock_get_album.return_value = mock_db_album
            mock_get_media.return_value = expected_media

            # GET request (not POST) to /media
            response = client.get(f"/albums/{album_id}/media")
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "media_items" in json_response
            assert len(json_response["media_items"]) == 2

            mock_get_media.assert_called_once_with(album_id)

    def test_remove_media_from_album_success(self, mock_db_album):
        """
        Test successfully removing a media item from an album.
        """
        album_id = mock_db_album["album_id"]
        media_id = "img-1"

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_remove_media_from_album"
        ) as mock_remove:
            mock_get_album.return_value = mock_db_album
            mock_remove.return_value = None

            # Updated endpoint: /media/{media_id}
            response = client.delete(f"/albums/{album_id}/media/{media_id}")
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "msg" in json_response
            assert "removed" in json_response["msg"].lower()

            mock_remove.assert_called_once_with(album_id, media_id)