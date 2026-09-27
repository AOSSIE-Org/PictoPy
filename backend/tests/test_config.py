import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.config import router as config_router
from app.config.settings import (
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(config_router, prefix="/config")
    return TestClient(app)


def test_supported_extensions_returns_all_configured_formats(client: TestClient):
    response = client.get("/config/supported-extensions")
    assert response.status_code == 200

    body = response.json()
    extensions = body["data"]["extensions"]

    expected = {
        ext.lstrip(".")
        for ext in SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS
    }
    assert set(extensions) == expected


def test_supported_extensions_have_no_leading_dot(client: TestClient):
    response = client.get("/config/supported-extensions")
    extensions = response.json()["data"]["extensions"]

    assert all(not ext.startswith(".") for ext in extensions)


def test_supported_extensions_is_sorted(client: TestClient):
    response = client.get("/config/supported-extensions")
    extensions = response.json()["data"]["extensions"]

    assert extensions == sorted(extensions)