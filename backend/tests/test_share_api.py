
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import share as share_routes


app = FastAPI()
app.include_router(share_routes.router, prefix="/share")
client = TestClient(app)


def setup_mocks(monkeypatch, is_locked):
    monkeypatch.setattr(
        share_routes,
        "db_get_album",
        lambda album_id: {"is_locked": is_locked},
    )

    monkeypatch.setattr(
        share_routes,
        "verify_album_password",
        lambda album_id, password: password == "correct-password",
    )

    create_mock = AsyncMock(return_value=object())
    monkeypatch.setattr(share_routes, "share_util_create", create_mock)

    monkeypatch.setattr(share_routes, "share_server_port", lambda: 52125)

    monkeypatch.setattr(
        share_routes,
        "share_util_describe",
        lambda entry, port: {
            "token": "test-token",
            "album_id": "album-1",
            "album_name": "Test Album",
            "image_count": 2,
            "port": port,
            "created_at": "2026-11-26T12:00:00",
            "expires_at": None,
            "is_protected": False,
            "urls": [],
        },
    )

    return create_mock


def test_unlocked_album_can_be_shared_without_password(monkeypatch):
    create_mock = setup_mocks(monkeypatch, is_locked=False)

    response = client.post("/share/albums/album-1", json={})

    assert response.status_code == 200
    assert response.json()["success"] is True
    create_mock.assert_awaited_once()


def test_locked_album_requires_password(monkeypatch):
    create_mock = setup_mocks(monkeypatch, is_locked=True)

    response = client.post("/share/albums/album-1", json={})

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Password Required"
    create_mock.assert_not_awaited()


def test_locked_album_rejects_wrong_password(monkeypatch):
    create_mock = setup_mocks(monkeypatch, is_locked=True)

    response = client.post(
        "/share/albums/album-1",
        json={"album_password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Invalid Password"
    create_mock.assert_not_awaited()


def test_locked_album_can_be_shared_with_correct_password(monkeypatch):
    create_mock = setup_mocks(monkeypatch, is_locked=True)

    response = client.post(
        "/share/albums/album-1",
        json={"album_password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    create_mock.assert_awaited_once()
