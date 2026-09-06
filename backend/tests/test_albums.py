import sys
import os
import pytest
import bcrypt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid
from typing import Any, Optional

from app.database.albums import AlbumRow
from app.routes import albums as albums_router

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = FastAPI()
app.include_router(albums_router.router, prefix="/albums", tags=["albums"])

client = TestClient(app)

# ##############################
# Pytest Fixtures
# ##############################


def album_row(
    album: dict[str, Any],
    cover_image_path: Optional[str] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> AlbumRow:
    """
    An albums row as the database helpers return it.

    Built as the production AlbumRow rather than a look-alike dict, so a
    column added there fails here instead of drifting silently.
    """
    return AlbumRow(
        album_id=album["album_id"],
        album_name=album["album_name"],
        description=album["description"],
        is_locked=album["is_locked"],
        password_hash=album["password_hash"],
        cover_image_path=cover_image_path,
        created_at=created_at,
        updated_at=updated_at,
    )


@pytest.fixture
def mock_db_album():
    return {
        "album_id": str(uuid.uuid4()),
        "album_name": "Summer Vacation",
        "description": "Photos from our 2023 summer trip.",
        "is_locked": False,
        "password_hash": None,
    }


@pytest.fixture
def mock_memory() -> dict[str, Any]:
    """A memories row as db_get_memory returns it, trimmed to what the route reads."""
    return {
        "memory_id": str(uuid.uuid4()),
        "title": "3 years ago in Paris",
        "subtitle": "July 2022 · Paris",
    }


@pytest.fixture
def mock_memory_images() -> list[dict[str, Any]]:
    return [
        {"id": str(uuid.uuid4()), "sort_order": 0},
        {"id": str(uuid.uuid4()), "sort_order": 1},
    ]


@pytest.fixture
def mock_db_locked_album():
    return {
        "album_id": str(uuid.uuid4()),
        "album_name": "Secret Party",
        "description": "Don't tell anyone.",
        "is_locked": True,
        "password_hash": "a_very_secure_hash",
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
                "is_locked": False,
                "password": None,
            },
            {
                "name": "Secret Vault",
                "description": "Hidden memories.",
                "is_locked": True,
                "password": "supersecret",
            },
        ],
    )
    def test_create_album_variants(self, album_data):
        with patch("app.routes.albums.db_get_album_by_name") as mock_get_by_name, patch(
            "app.routes.albums.db_insert_album"
        ) as mock_insert:
            mock_get_by_name.return_value = None  # No existing album
            mock_insert.return_value = None

            response = client.post("/albums/", json=album_data)
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "album_id" in json_response

            mock_insert.assert_called_once()
            # Verify that the album_id is a valid UUID
            album_id = json_response["album_id"]
            uuid.UUID(album_id)  # This will raise ValueError if not a valid UUID

    def test_create_album_duplicate_name(self):
        """Test creating album with duplicate name."""
        album_data = {
            "name": "Existing Album",
            "description": "This name already exists",
            "is_locked": False,
            "password": None,
        }

        with patch("app.routes.albums.db_get_album_by_name") as mock_get_by_name:
            mock_get_by_name.return_value = album_row(
                {
                    "album_id": "existing-id",
                    "album_name": "Existing Album",
                    "description": "desc",
                    "is_locked": False,
                    "password_hash": None,
                }
            )

            response = client.post("/albums/", json=album_data)
            assert response.status_code == 409

            json_response = response.json()
            assert json_response["detail"]["success"] is False
            assert json_response["detail"]["error"] == "Album Already Exists"

    def test_get_all_albums_public_only(self, mock_db_album):
        """
        Test fetching all albums.
        """
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            mock_get_all.return_value = [
                album_row(
                    mock_db_album,
                    created_at="2026-08-01 09:00:00",
                    updated_at="2026-08-05 09:00:00",
                )
            ]

            response = client.get("/albums/")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert isinstance(json_response["albums"], list)
            assert len(json_response["albums"]) == 1
            assert json_response["albums"][0]["album_id"] == mock_db_album["album_id"]
            assert (
                json_response["albums"][0]["album_name"] == mock_db_album["album_name"]
            )
            assert (
                json_response["albums"][0]["description"]
                == mock_db_album["description"]
            )
            assert json_response["albums"][0]["is_locked"] == mock_db_album["is_locked"]

            mock_get_all.assert_called_once()

    def test_get_all_albums_include_hidden(self, mock_db_album, mock_db_locked_album):
        """
        Test fetching all albums including locked ones.
        """
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            mock_get_all.return_value = [
                album_row(
                    mock_db_album,
                    created_at="2026-08-01 09:00:00",
                    updated_at="2026-08-05 09:00:00",
                ),
                album_row(
                    mock_db_locked_album,
                    created_at="2026-08-02 09:00:00",
                    updated_at="2026-08-06 09:00:00",
                ),
            ]

            response = client.get("/albums/")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert isinstance(json_response["albums"], list)
            assert len(json_response["albums"]) == 2

            ids = {album["album_id"] for album in json_response["albums"]}
            assert mock_db_album["album_id"] in ids
            assert mock_db_locked_album["album_id"] in ids

            mock_get_all.assert_called_once()

    def test_locked_album_cover_is_withheld(self, mock_db_album, mock_db_locked_album):
        """A locked album's cover would reveal the content the password gates."""
        with patch("app.routes.albums.db_get_all_albums") as mock_get_all, patch(
            "app.routes.albums.db_get_album_cover_path"
        ) as mock_cover:
            mock_get_all.return_value = [
                album_row(
                    mock_db_album,
                    created_at="2026-08-01 09:00:00",
                    updated_at="2026-08-05 09:00:00",
                ),
                album_row(
                    mock_db_locked_album,
                    created_at="2026-08-02 09:00:00",
                    updated_at="2026-08-06 09:00:00",
                ),
            ]
            mock_cover.return_value = "/photos/secret.jpg"

            response = client.get("/albums/")
            assert response.status_code == 200

            covers = {
                album["album_id"]: album["cover_image_path"]
                for album in response.json()["albums"]
            }
            assert covers[mock_db_album["album_id"]] == "/photos/secret.jpg"
            assert covers[mock_db_locked_album["album_id"]] is None
            # The path is never even looked up for a locked album
            mock_cover.assert_called_once_with(mock_db_album["album_id"])

    def test_get_album_by_id_withholds_a_locked_cover(self, mock_db_locked_album):
        """The single-album read must not leak what the listing hides."""
        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_get_album_cover_path"
        ) as mock_cover:
            mock_get_album.return_value = album_row(
                mock_db_locked_album,
                created_at="2026-08-02 09:00:00",
                updated_at="2026-08-06 09:00:00",
            )
            mock_cover.return_value = "/photos/secret.jpg"

            response = client.get(f"/albums/{mock_db_locked_album['album_id']}")
            assert response.status_code == 200
            assert response.json()["data"]["cover_image_path"] is None
            mock_cover.assert_not_called()

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

            mock_get_all.assert_called_once()

    def test_get_album_by_id_success(self, mock_db_album):
        """
        Test fetching a single album by its ID successfully.
        """
        with patch("app.routes.albums.db_get_album") as mock_get_album:
            mock_get_album.return_value = album_row(
                mock_db_album,
                created_at="2026-08-01 09:00:00",
                updated_at="2026-08-05 09:00:00",
            )

            response = client.get(f"/albums/{mock_db_album['album_id']}")
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert json_response["data"]["album_id"] == mock_db_album["album_id"]
            assert json_response["data"]["album_name"] == mock_db_album["album_name"]
            assert json_response["data"]["description"] == mock_db_album["description"]
            assert json_response["data"]["is_locked"] == mock_db_album["is_locked"]
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
            assert json_response["detail"]["message"] == "Album not found"
            assert json_response["detail"]["success"] is False
            mock_get_album.assert_called_once_with(non_existent_id)

    @pytest.mark.parametrize(
        "album_data, request_data, verify_password_return, expected_status",
        [
            # Case 1: Public album (no password protection)
            (
                album_row(
                    {
                        "album_id": "abc-123",
                        "album_name": "Old Name",
                        "description": "Old Desc",
                        "is_locked": False,
                        "password_hash": None,
                    }
                ),
                {
                    "name": "Updated Public Album",
                    "description": "Updated description",
                    "is_locked": False,
                    "password": None,
                    "current_password": None,
                },
                True,
                200,
            ),
            # Case 2: Locked album with correct current password
            (
                album_row(
                    {
                        "album_id": "abc-456",
                        "album_name": "Locked Album",
                        "description": "Secret",
                        "is_locked": True,
                        "password_hash": bcrypt.hashpw(
                            b"oldpass", bcrypt.gensalt()
                        ).decode(),
                    }
                ),
                {
                    "name": "Updated Locked Album",
                    "description": "Updated locked description",
                    "is_locked": True,
                    "password": "newpass123",
                    "current_password": "oldpass",
                },
                True,
                200,
            ),
            # Case 3: Locked album with incorrect current password
            (
                album_row(
                    {
                        "album_id": "abc-789",
                        "album_name": "Locked Album",
                        "description": "Secret",
                        "is_locked": True,
                        "password_hash": bcrypt.hashpw(
                            b"correctpass", bcrypt.gensalt()
                        ).decode(),
                    }
                ),
                {
                    "name": "Invalid Attempt",
                    "description": "Wrong password used",
                    "is_locked": True,
                    "password": "newpass123",
                    "current_password": "wrongpass",
                },
                False,
                401,
            ),
        ],
    )
    def test_update_album(
        self, album_data, request_data, verify_password_return, expected_status
    ):
        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_update_album"
        ) as mock_update_album, patch(
            "app.routes.albums.verify_album_password"
        ) as mock_verify:
            mock_get_album.return_value = album_data
            mock_verify.return_value = verify_password_return

            response = client.put(
                f"/albums/{album_data['album_id']}", json=request_data
            )
            assert response.status_code == expected_status

            if expected_status == 200:
                assert response.json()["success"] is True
                assert "msg" in response.json()
                mock_update_album.assert_called_once()
            else:
                mock_update_album.assert_not_called()

    def test_delete_album_success(self, mock_db_album):
        """
        Test successfully deleting an existing album.
        """
        album_id = mock_db_album["album_id"]
        album_tuple = album_row(mock_db_album)

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_delete_album"
        ) as mock_delete_album:
            mock_get_album.return_value = album_tuple
            mock_delete_album.return_value = None

            response = client.delete(f"/albums/{album_id}")

            assert response.status_code == 200
            json_response = response.json()

            assert json_response["success"] is True
            assert json_response["msg"] == "Album deleted successfully"
            mock_delete_album.assert_called_once_with(album_id)


class TestAlbumImageManagement:
    """
    Test suite for routes managing images within albums.
    """

    def test_add_images_to_album_success(self, mock_db_album):
        """
        Test adding valid images to an existing album.
        """
        album_id = mock_db_album["album_id"]
        request_body = {
            "image_ids": [
                "71abff29-27b4-43a4-9e76-b78504bea325",
                "2d4bff29-1111-43a4-9e76-b78504bea999",
            ]
        }

        album_tuple = album_row(mock_db_album)

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_add_images_to_album"
        ) as mock_add_images:
            mock_get_album.return_value = album_tuple
            mock_add_images.return_value = None

            response = client.post(f"/albums/{album_id}/images", json=request_body)
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "msg" in json_response
            assert f"{len(request_body['image_ids'])} images" in json_response["msg"]

            mock_get_album.assert_called_once_with(album_id)
            mock_add_images.assert_called_once_with(album_id, request_body["image_ids"])

    def test_get_album_images_success(self, mock_db_album):
        """
        Test retrieving image IDs from an existing album.
        """
        album_id = mock_db_album["album_id"]
        expected_image_ids = [
            "71abff29-27b4-43a4-9e76-b78504bea325",
            "2d4bff29-1111-43a4-9e76-b78504bea999",
        ]

        album_tuple = album_row(mock_db_album)

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_get_album_images"
        ) as mock_get_images:
            mock_get_album.return_value = album_tuple
            mock_get_images.return_value = expected_image_ids

            response = client.post(f"/albums/{album_id}/images/get", json={})
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "image_ids" in json_response
            assert set(json_response["image_ids"]) == set(expected_image_ids)

            mock_get_album.assert_called_once_with(album_id)
            mock_get_images.assert_called_once_with(album_id)

    def test_remove_image_from_album_success(self, mock_db_album):
        """
        Test successfully removing an image from an album.
        """
        album_id = mock_db_album["album_id"]
        image_id = "71abff29-27b4-43a4-9e76-b78504bea325"

        album_tuple = album_row(mock_db_album)

        with patch("app.routes.albums.db_get_album") as mock_get_album, patch(
            "app.routes.albums.db_remove_image_from_album"
        ) as mock_remove:
            mock_get_album.return_value = album_tuple
            mock_remove.return_value = None

            response = client.delete(f"/albums/{album_id}/images/{image_id}")
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert "msg" in json_response
            assert "successfully" in json_response["msg"].lower()

            mock_get_album.assert_called_once_with(album_id)
            mock_remove.assert_called_once_with(album_id, image_id)

    def test_remove_multiple_images_from_album(self, mock_db_album):
        """
        Test removing multiple images from an album using the bulk delete endpoint.
        """
        album_id = mock_db_album["album_id"]
        image_ids_to_remove = {"image_ids": [str(uuid.uuid4()), str(uuid.uuid4())]}

        with patch("app.routes.albums.db_get_album") as mock_get, patch(
            "app.routes.albums.db_remove_images_from_album"
        ) as mock_remove_bulk:
            mock_get.return_value = album_row(mock_db_album)
            response = client.request(
                "DELETE", f"/albums/{album_id}/images", json=image_ids_to_remove
            )
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["success"] is True
            assert str(len(image_ids_to_remove["image_ids"])) in json_response["msg"]
            mock_get.assert_called_once_with(album_id)
            mock_remove_bulk.assert_called_once_with(
                album_id, image_ids_to_remove["image_ids"]
            )


class TestCreateAlbumFromMemory:
    """Test suite for converting a curated memory into an album."""

    def test_create_album_from_memory_success(
        self, mock_memory: dict[str, Any], mock_memory_images: list[dict[str, Any]]
    ) -> None:
        with patch("app.utils.albums.db_get_memory") as mock_get_memory, patch(
            "app.utils.albums.db_get_memory_images"
        ) as mock_get_images, patch(
            "app.utils.albums.db_get_album_by_name"
        ) as mock_get_by_name, patch(
            "app.utils.albums.db_create_album_with_images"
        ) as mock_create:
            mock_get_memory.return_value = mock_memory
            mock_get_images.return_value = mock_memory_images
            mock_get_by_name.return_value = None
            mock_create.return_value = len(mock_memory_images)

            response = client.post(
                "/albums/from-memory",
                json={"memory_id": mock_memory["memory_id"], "name": "Paris 2022"},
            )
            assert response.status_code == 200

            json_response = response.json()
            assert json_response["success"] is True
            assert json_response["data"]["image_count"] == len(mock_memory_images)
            uuid.UUID(json_response["data"]["album_id"])

            # The memory's subtitle becomes the album description, and only the
            # image ids are handed over - clips are left behind.
            album_id, name, description, image_ids = mock_create.call_args.args
            # The id that was persisted has to be the one handed back, or the
            # client navigates to an album that does not exist.
            assert album_id == json_response["data"]["album_id"]
            assert name == "Paris 2022"
            assert description == mock_memory["subtitle"]
            assert image_ids == [image["id"] for image in mock_memory_images]

    @pytest.mark.parametrize(
        "payload",
        [
            {"memory_id": "mem-1", "name": "   "},
            {"memory_id": "   ", "name": "Paris 2022"},
        ],
    )
    def test_create_album_from_memory_rejects_blank_fields(
        self, payload: dict[str, str]
    ) -> None:
        """A name of spaces satisfies min_length but is not a name."""
        with patch("app.utils.albums.db_create_album_with_images") as mock_create:
            response = client.post("/albums/from-memory", json=payload)

            assert response.status_code == 422
            mock_create.assert_not_called()

    def test_create_album_from_memory_trims_the_name(
        self, mock_memory: dict[str, Any], mock_memory_images: list[dict[str, Any]]
    ) -> None:
        with patch("app.utils.albums.db_get_memory") as mock_get_memory, patch(
            "app.utils.albums.db_get_memory_images"
        ) as mock_get_images, patch(
            "app.utils.albums.db_get_album_by_name"
        ) as mock_get_by_name, patch(
            "app.utils.albums.db_create_album_with_images"
        ) as mock_create:
            mock_get_memory.return_value = mock_memory
            mock_get_images.return_value = mock_memory_images
            mock_get_by_name.return_value = None
            mock_create.return_value = len(mock_memory_images)

            response = client.post(
                "/albums/from-memory",
                json={"memory_id": mock_memory["memory_id"], "name": "  Paris  "},
            )

            assert response.status_code == 200
            assert mock_create.call_args.args[1] == "Paris"

    def test_create_album_from_memory_not_found(self) -> None:
        with patch("app.utils.albums.db_get_memory") as mock_get_memory:
            mock_get_memory.return_value = None

            response = client.post(
                "/albums/from-memory",
                json={"memory_id": str(uuid.uuid4()), "name": "Paris 2022"},
            )
            assert response.status_code == 404
            assert response.json()["detail"]["error"] == "Memory Not Found"

    def test_create_album_from_empty_memory(self, mock_memory: dict[str, Any]) -> None:
        """A memory with no photos cannot become an album."""
        with patch("app.utils.albums.db_get_memory") as mock_get_memory, patch(
            "app.utils.albums.db_get_memory_images"
        ) as mock_get_images, patch(
            "app.utils.albums.db_create_album_with_images"
        ) as mock_create:
            mock_get_memory.return_value = mock_memory
            mock_get_images.return_value = []

            response = client.post(
                "/albums/from-memory",
                json={"memory_id": mock_memory["memory_id"], "name": "Paris 2022"},
            )
            assert response.status_code == 400
            assert response.json()["detail"]["error"] == "Empty Memory"
            mock_create.assert_not_called()

    def test_create_album_from_memory_duplicate_name(
        self,
        mock_memory: dict[str, Any],
        mock_memory_images: list[dict[str, Any]],
        mock_db_album: dict[str, Any],
    ) -> None:
        with patch("app.utils.albums.db_get_memory") as mock_get_memory, patch(
            "app.utils.albums.db_get_memory_images"
        ) as mock_get_images, patch(
            "app.utils.albums.db_get_album_by_name"
        ) as mock_get_by_name, patch(
            "app.utils.albums.db_create_album_with_images"
        ) as mock_create:
            mock_get_memory.return_value = mock_memory
            mock_get_images.return_value = mock_memory_images
            mock_get_by_name.return_value = album_row(mock_db_album)

            response = client.post(
                "/albums/from-memory",
                json={
                    "memory_id": mock_memory["memory_id"],
                    "name": mock_db_album["album_name"],
                },
            )
            assert response.status_code == 409
            assert response.json()["detail"]["error"] == "Album Already Exists"
            mock_create.assert_not_called()


class TestAlbumRouteErrors:
    """Test suite for verifying that album routes correctly handle exceptions."""

    def test_unexpected_exceptions_mapped_to_500(self):
        """Verify that an unexpected exception returns a 500 error."""
        from unittest.mock import patch

        with patch("app.routes.albums.db_get_all_albums") as mock_get_all:
            mock_get_all.side_effect = Exception("Database explosion")
            response = client.get("/albums/")
            assert response.status_code == 500
            json_resp = response.json()
            assert json_resp["detail"]["success"] is False
            assert "unexpected error" in json_resp["detail"]["message"].lower()

    def test_duplicate_album_integrity_error(self):
        """Verify that a database IntegrityError returns a 409 conflict."""
        import sqlite3
        from unittest.mock import patch

        with patch("app.routes.albums.db_get_album_by_name", return_value=None):
            with patch(
                "app.routes.albums.db_insert_album",
                side_effect=sqlite3.IntegrityError("Unique constraint failed"),
            ):
                response = client.post(
                    "/albums/",
                    json={"name": "Duplicate", "description": "This should fail"},
                )
                assert response.status_code == 409
                json_resp = response.json()
                assert json_resp["detail"]["success"] is False
                assert "album already exists" in json_resp["detail"]["error"].lower()
