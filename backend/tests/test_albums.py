import sys
import os
import album
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


# NOTE FOR MAINTAINERS:
# We patch db_* call-sites in app.routes.albums in ONE place (fixture) instead of patching
# individual helpers inside each test. This keeps tests focused on observable API behavior
# and reduces coupling/duplication in the test suite.
#
# This is the best "tests-only" approach without changing albums.py to use DI/DB boundary.


# -----------------------------
# Fake DB (in-memory behavior)
# Matches the signatures used by albums.py
# -----------------------------
class FakeDB:
    def __init__(self):
        # album_id -> dict
        self.albums = {}
        # album_id -> set(image_ids)
        self.album_images = {}

    # db_get_all_albums(show_hidden: bool)
    def get_all_albums(self, show_hidden: bool):
        rows = []
        for a in self.albums.values():
            if show_hidden or not a["is_hidden"]:
                rows.append(
                    (
                        a["album_id"],
                        a["album_name"],
                        a["description"],
                        int(a["is_hidden"]),
                    )
                )
        return rows

    # db_get_album_by_name(name: str)
    def get_album_by_name(self, name: str):
        for a in self.albums.values():
            if a["album_name"] == name:
                # albums.py uses existing_album truthiness only, but keep shape similar
                return (
                    a["album_id"],
                    a["album_name"],
                    a["description"],
                    int(a["is_hidden"]),
                    a["password_hash"],
                )
        return None

    # db_get_album(album_id: str) -> tuple or None
    def get_album(self, album_id: str):
        a = self.albums.get(album_id)
        if not a:
            return None
        return (
            a["album_id"],
            a["album_name"],
            a["description"],
            int(a["is_hidden"]),
            a["password_hash"],
        )

    # db_insert_album(album_id, name, description, is_hidden, password)
    def insert_album(self, album_id: str, name: str, description: str, is_hidden: bool, password):
        # store "password" as password_hash slot because albums.py expects album[4]
        self.albums[album_id] = {
            "album_id": album_id,
            "album_name": name,
            "description": description or "",
            "is_hidden": bool(is_hidden),
            "password_hash": password,
        }
        return None

# db_update_album(album_id, name, description, is_hidden, password)
    def update_album(self, album_id: str, name: str, description: str, is_hidden: bool, password):
        if album_id not in self.albums:
            raise ValueError("Album not found")

        album = self.albums[album_id]
        album["album_name"] = name
        album["description"] = description or ""
        album["is_hidden"] = bool(is_hidden)

    # Match real DB behavior
        if password is not None:
            album["password_hash"] = password

        return None

    # db_delete_album(album_id)
    def delete_album(self, album_id: str):
        self.albums.pop(album_id, None)
        self.album_images.pop(album_id, None)
        return None

    # db_get_album_images(album_id) -> list[str]
    def get_album_images(self, album_id: str):
        return list(self.album_images.get(album_id, set()))

    # db_add_images_to_album(album_id, image_ids)
    def add_images_to_album(self, album_id: str, image_ids):
        self.album_images.setdefault(album_id, set()).update(image_ids)
        return None

    # db_remove_image_from_album(album_id, image_id)
    def remove_image_from_album(self, album_id: str, image_id: str):
        self.album_images.setdefault(album_id, set()).discard(image_id)
        return None

    # db_remove_images_from_album(album_id, image_ids)
    def remove_images_from_album(self, album_id: str, image_ids):
        s = self.album_images.setdefault(album_id, set())
        for i in image_ids:
            s.discard(i)
        return None


@pytest.fixture
def fake_db():
    return FakeDB()


@pytest.fixture
def client(fake_db):
    # Patch all db_* names ONCE where they are used (app.routes.albums),
    # so individual tests don't patch internal helpers.
    with patch.multiple(
        "app.routes.albums",
        db_get_all_albums=fake_db.get_all_albums,
        db_get_album_by_name=fake_db.get_album_by_name,
        db_get_album=fake_db.get_album,
        db_insert_album=fake_db.insert_album,
        db_update_album=fake_db.update_album,
        db_delete_album=fake_db.delete_album,
        db_get_album_images=fake_db.get_album_images,
        db_add_images_to_album=fake_db.add_images_to_album,
        db_remove_image_from_album=fake_db.remove_image_from_album,
        db_remove_images_from_album=fake_db.remove_images_from_album,
    ):
        yield TestClient(app)


# -----------------------------
# Tests (API behavior focused)
# -----------------------------
class TestAlbumRoutes:
    @pytest.mark.parametrize(
        "album_data",
        [
            {
                "name": "New Year's Eve",
                "description": "Party photos from 2024.",
                "is_hidden": False,
                "password": None,
            },
            {
                "name": "Secret Vault",
                "description": "Hidden memories.",
                "is_hidden": True,
                "password": "supersecret",
            },
        ],
    )
    def test_create_album_variants(self, client, album_data):
        response = client.post("/albums/", json=album_data)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert "album_id" in body
        # albums.py generates UUIDs with uuid4
        uuid.UUID(body["album_id"])

    def test_create_album_duplicate_name(self, client):
        album_data = {
            "name": "Existing Album",
            "description": "This name already exists",
            "is_hidden": False,
            "password": None,
        }

        r1 = client.post("/albums/", json=album_data)
        assert r1.status_code == 200

        r2 = client.post("/albums/", json=album_data)
        assert r2.status_code == 409

        body = r2.json()
        assert body["detail"]["success"] is False
        assert body["detail"]["error"] == "Album Already Exists"

    def test_get_all_albums_public_only(self, client):
        # create one public, one hidden
        client.post("/albums/", json={"name": "Public", "description": "d", "is_hidden": False, "password": None})
        client.post("/albums/", json={"name": "Hidden", "description": "d", "is_hidden": True, "password": "x"})

        r = client.get("/albums/")
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert isinstance(body["albums"], list)
        assert len(body["albums"]) == 1
        assert body["albums"][0]["album_name"] == "Public"
        assert body["albums"][0]["is_hidden"] is False

    def test_get_all_albums_include_hidden(self, client):
        client.post("/albums/", json={"name": "Public", "description": "d", "is_hidden": False, "password": None})
        client.post("/albums/", json={"name": "Hidden", "description": "d", "is_hidden": True, "password": "x"})

        r = client.get("/albums/?show_hidden=true")
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert isinstance(body["albums"], list)
        assert len(body["albums"]) == 2

    def test_get_all_albums_empty_list(self, client):
        r = client.get("/albums/")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["albums"] == []

    def test_get_album_by_id_success(self, client):
        created = client.post("/albums/", json={"name": "A", "description": "D", "is_hidden": False, "password": None})
        assert created.status_code == 200
        album_id = created.json()["album_id"]

        r = client.get(f"/albums/{album_id}")
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert body["data"]["album_id"] == album_id
        assert body["data"]["album_name"] == "A"
        assert body["data"]["description"] == "D"
        assert body["data"]["is_hidden"] is False

    def test_get_album_by_id_not_found(self, client):
        non_existent_id = str(uuid.uuid4())
        r = client.get(f"/albums/{non_existent_id}")
        assert r.status_code == 404

        body = r.json()
        assert body["detail"]["error"] == "Album Not Found"
        assert body["detail"]["message"] == "Album not found"
        assert body["detail"]["success"] is False

    @pytest.mark.parametrize(
        "is_hidden, current_password, verify_ok, expected_status",
        [
            (False, None, True, 200),      # public update
            (True, "oldpass", True, 200),  # hidden correct password
            (True, "wrongpass", False, 401),  # hidden wrong password
        ],
    )
    def test_update_album(self, client, is_hidden, current_password, verify_ok, expected_status):
        created = client.post(
            "/albums/",
            json={
                "name": "Album",
                "description": "Desc",
                "is_hidden": is_hidden,
                "password": "oldpass" if is_hidden else None,
            },
        )
        album_id = created.json()["album_id"]

        update_payload = {
            "name": "Updated Name",
            "description": "Updated description",
            "is_hidden": is_hidden,
            "password": "newpass123" if is_hidden else None,
            "current_password": current_password,
        }

        # Patch password verification only (pure business logic, not DB I/O)
        with patch("app.routes.albums.verify_album_password", return_value=verify_ok):
            r = client.put(f"/albums/{album_id}", json=update_payload)

        assert r.status_code == expected_status
        body = r.json()

        if expected_status == 200:
            assert body["success"] is True
            assert body["msg"] == "Album updated successfully"
        else:
            assert body["detail"]["success"] is False

    def test_delete_album_success(self, client):
        created = client.post("/albums/", json={"name": "ToDelete", "description": "d", "is_hidden": False, "password": None})
        album_id = created.json()["album_id"]

        r = client.delete(f"/albums/{album_id}")
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert body["msg"] == "Album deleted successfully"


class TestAlbumImageManagement:
    def test_add_images_to_album_success(self, client):
        created = client.post("/albums/", json={"name": "A", "description": "d", "is_hidden": False, "password": None})
        album_id = created.json()["album_id"]

        request_body = {
            "image_ids": [
                "71abff29-27b4-43a4-9e76-b78504bea325",
                "2d4bff29-1111-43a4-9e76-b78504bea999",
            ]
        }

        r = client.post(f"/albums/{album_id}/images", json=request_body)
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert str(len(request_body["image_ids"])) in body["msg"]

    def test_get_album_images_success(self, client):
        # Create hidden album because /images/get checks password if hidden
        created = client.post("/albums/", json={"name": "Hidden", "description": "d", "is_hidden": True, "password": "pw"})
        album_id = created.json()["album_id"]

        image_ids = [
            "71abff29-27b4-43a4-9e76-b78504bea325",
            "2d4bff29-1111-43a4-9e76-b78504bea999",
        ]
        client.post(f"/albums/{album_id}/images", json={"image_ids": image_ids})

        # Patch verify_album_password so the hidden album check passes
        with patch("app.routes.albums.verify_album_password", return_value=True):
            r = client.post(f"/albums/{album_id}/images/get", json={"password": "pw"})

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert set(body["image_ids"]) == set(image_ids)

    def test_remove_image_from_album_success(self, client):
        created = client.post("/albums/", json={"name": "A", "description": "d", "is_hidden": False, "password": None})
        album_id = created.json()["album_id"]

        image_id = "71abff29-27b4-43a4-9e76-b78504bea325"
        client.post(f"/albums/{album_id}/images", json={"image_ids": [image_id]})

        r = client.delete(f"/albums/{album_id}/images/{image_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True

    def test_remove_multiple_images_from_album(self, client):
        created = client.post("/albums/", json={"name": "A", "description": "d", "is_hidden": False, "password": None})
        album_id = created.json()["album_id"]

        ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        client.post(f"/albums/{album_id}/images", json={"image_ids": ids})

        r = client.request("DELETE", f"/albums/{album_id}/images", json={"image_ids": ids})
        assert r.status_code == 200
        body = r.json()

        assert body["success"] is True
        assert str(len(ids)) in body["msg"]
