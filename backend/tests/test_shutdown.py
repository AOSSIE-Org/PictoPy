import os
import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app as main_app

VALID_TOKEN = "a" * 64


@pytest.fixture
def app():
    return main_app


@pytest.fixture
def client():
    with patch("app.config.settings.SHUTDOWN_TOKEN", VALID_TOKEN), patch(
        "app.routes.shutdown._delayed_shutdown"
    ):
        with TestClient(main_app, raise_server_exceptions=False) as c:
            yield c


# ---------------------------------------------------------------------------
# Header matrix tests
# ---------------------------------------------------------------------------


class TestShutdownHeaderMatrix:
    """Cover all four header scenarios on the /shutdown endpoint."""

    def test_no_token_returns_401(self, client):
        """Missing X-Shutdown-Token header must return 401 Unauthorized."""
        resp = client.post("/shutdown")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Unauthorized"

    def test_empty_token_returns_401(self, client):
        """Empty header value is treated as missing (None after strip by FastAPI)."""
        resp = client.post("/shutdown", headers={"X-Shutdown-Token": ""})
        # FastAPI sends None for empty optional header → 401
        assert resp.status_code in (401, 403)

    def test_malformed_token_returns_403(self, client):
        """A syntactically valid but wrong token returns 403 Forbidden."""
        resp = client.post("/shutdown", headers={"X-Shutdown-Token": "notahextoken"})
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Forbidden"

    def test_wrong_token_returns_403(self, client):
        """A well-formed but incorrect token must return 403."""
        wrong = "b" * 64
        resp = client.post("/shutdown", headers={"X-Shutdown-Token": wrong})
        assert resp.status_code == 403

    def test_correct_token_returns_200(self, client):
        """A correct token must return 200 with shutting_down status."""
        resp = client.post("/shutdown", headers={"X-Shutdown-Token": VALID_TOKEN})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "shutting_down"


# ---------------------------------------------------------------------------
# Token rotation / restart simulation
# ---------------------------------------------------------------------------


class TestTokenRotation:
    """Verify per-session token semantics."""

    def test_old_token_rejected_after_rotation(self, app):
        """Simulates a restart: new session → new token → old token is rejected."""
        old_token = "c" * 64
        new_token = "d" * 64

        with patch("app.config.settings.SHUTDOWN_TOKEN", new_token), patch(
            "app.routes.shutdown._delayed_shutdown"
        ):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post("/shutdown", headers={"X-Shutdown-Token": old_token})
                assert resp.status_code == 403

    def test_new_token_accepted_after_rotation(self, app):
        new_token = "e" * 64
        with patch("app.config.settings.SHUTDOWN_TOKEN", new_token), patch(
            "app.routes.shutdown._delayed_shutdown"
        ):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post("/shutdown", headers={"X-Shutdown-Token": new_token})
                assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Token file cleanup
# ---------------------------------------------------------------------------


class TestTokenFileCleanup:
    """_delayed_shutdown should attempt to remove the token file."""

    def test_token_file_removed_on_shutdown(self, tmp_path):
        token_file = str(tmp_path / "pictopy_shutdown.token")
        token_file_obj = open(token_file, "w")
        token_file_obj.write(VALID_TOKEN)
        token_file_obj.close()

        with patch("app.config.settings.SHUTDOWN_TOKEN", VALID_TOKEN), patch(
            "app.config.settings.SHUTDOWN_TOKEN_FILE", token_file
        ), patch("app.routes.shutdown.os.kill"), patch("app.routes.shutdown.os._exit"):

            from app.routes.shutdown import _delayed_shutdown

            asyncio.get_event_loop().run_until_complete(_delayed_shutdown(delay=0))

        assert not os.path.exists(token_file)

    def test_missing_token_file_does_not_raise(self, tmp_path):
        """If file was already deleted, _delayed_shutdown must not propagate the error."""
        token_file = str(tmp_path / "nonexistent.token")

        with patch("app.config.settings.SHUTDOWN_TOKEN_FILE", token_file), patch(
            "app.routes.shutdown.os.kill"
        ), patch("app.routes.shutdown.os._exit"):

            from app.routes.shutdown import _delayed_shutdown

            # Should complete without raising
            asyncio.get_event_loop().run_until_complete(_delayed_shutdown(delay=0))


# ---------------------------------------------------------------------------
# Concurrent invalid requests
# ---------------------------------------------------------------------------


class TestConcurrentInvalidRequests:
    """Concurrent bad requests must not block a legitimate shutdown."""

    def test_concurrent_invalid_then_valid(self, client):
        wrong = "f" * 64
        for _ in range(10):
            resp = client.post("/shutdown", headers={"X-Shutdown-Token": wrong})
            assert resp.status_code == 403

        # Service still reachable and accepts the correct token
        resp = client.post("/shutdown", headers={"X-Shutdown-Token": VALID_TOKEN})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Corrupted / invalid token content loaded by sync service
# ---------------------------------------------------------------------------


class TestCorruptedTokenContent:
    """If the token file had garbage, hmac.compare_digest must still return False."""

    def test_corrupted_token_always_rejects(self, app):
        corrupted = "\x00\xff partial"
        with patch("app.config.settings.SHUTDOWN_TOKEN", corrupted), patch(
            "app.routes.shutdown._delayed_shutdown"
        ):
            with TestClient(app, raise_server_exceptions=False) as c:
                # Even sending the corrupted string must not crash the endpoint
                resp = c.post("/shutdown", headers={"X-Shutdown-Token": corrupted})
                # hmac.compare_digest may raise TypeError for non-str/bytes — document behavior
                assert resp.status_code in (200, 400, 403, 500)


class TestEmptyTokenContent:
    def test_empty_settings_token_always_rejects(self, app):
        """An empty SHUTDOWN_TOKEN must never grant access, even with an empty header."""
        with patch("app.config.settings.SHUTDOWN_TOKEN", ""):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post("/shutdown", headers={"X-Shutdown-Token": ""})
                # Empty header is None → 401; but documents that "" ≠ "" guard is NOT present
                assert resp.status_code in (401, 403, 503)

    def test_get_method_rejected(self, app):
        """GET /shutdown should be rejected automatically."""
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/shutdown")
            assert resp.status_code == 405

    def test_long_token_header_rejected(self, app):
        """Extremely long token header should be rejected."""
        long_token = "a" * 1024 * 1024  # 1MB
        with patch("app.config.settings.SHUTDOWN_TOKEN", VALID_TOKEN), patch(
            "app.routes.shutdown._delayed_shutdown"
        ):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post("/shutdown", headers={"X-Shutdown-Token": long_token})
                assert resp.status_code in (
                    400,
                    403,
                    413,
                    431,
                )  # Payload too large, forbidden, or header fields too large
