# ruff: noqa: E402 -- app imports must follow the database guard below.
import os

# settings.py picks the database once, at import, and only this flag points it
# away from the user's live library. Set before any app import so a local run
# can never touch it.
os.environ["GITHUB_ACTIONS"] = "true"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings

# If anything imported settings before this file, the flag came too late.
assert (
    os.path.basename(settings.DATABASE_PATH) == "test_db.sqlite3"
), f"refusing to run tests against {settings.DATABASE_PATH}"

from app.routes import health, shutdown


@pytest.fixture
def client():
    """TestClient over the routers under test, without main.py's startup side effects."""
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(shutdown.router)
    return TestClient(app)
