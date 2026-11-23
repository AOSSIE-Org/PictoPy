import asyncio
import sqlite3
import time
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.database import folders as db_folders
from app.routes import health


@pytest.mark.parametrize(
    "db_ok, watcher_running, expected",
    [
        (
            True,
            True,
            {"status": "healthy", "database": "connected", "watcher": "running"},
        ),
        (
            True,
            False,
            {"status": "healthy", "database": "connected", "watcher": "stopped"},
        ),
        (
            False,
            True,
            {"status": "unhealthy", "database": "disconnected", "watcher": "running"},
        ),
        (
            False,
            False,
            {"status": "unhealthy", "database": "disconnected", "watcher": "stopped"},
        ),
    ],
)
def test_health_reports_database_and_watcher_state(
    client: TestClient, db_ok: bool, watcher_running: bool, expected: dict
) -> None:
    """Verify health endpoint formats database connectivity and watcher process states."""
    with patch(
        "app.routes.health.db_check_database_connection", return_value=db_ok
    ), patch(
        "app.routes.health.watcher_util_is_watcher_running",
        return_value=watcher_running,
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == expected


def test_db_check_database_connection_real_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify db_check_database_connection against real SQLite files with and without tables."""
    db_path = str(tmp_path / "sync_health_test.sqlite3")
    monkeypatch.setattr(db_folders, "DATABASE_PATH", db_path)

    # Database file exists but folders table does not exist
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, val TEXT)")
    conn.commit()
    conn.close()

    assert db_folders.db_check_database_connection() is False

    # Create folders table
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE folders (folder_id TEXT PRIMARY KEY, folder_path TEXT)")
    conn.commit()
    conn.close()

    assert db_folders.db_check_database_connection() is True


@pytest.mark.asyncio
async def test_health_check_does_not_block_event_loop_during_slow_db() -> None:
    """Verify that a slow or delayed database operation inside the health-check
    endpoint does not block concurrent asynchronous requests on the main event loop.

    Because health_check() is defined as a standard def route, FastAPI executes
    it inside an external threadpool (run_in_threadpool), leaving the asyncio
    event loop unblocked to handle concurrent requests immediately.
    """
    app = FastAPI()
    app.include_router(health.router)

    # An async endpoint that must execute immediately if the event loop is free
    @app.get("/async-probe")
    async def async_probe() -> dict[str, str]:
        return {"status": "probe_ok"}

    delay_seconds = 0.30

    def slow_db_check() -> bool:
        time.sleep(delay_seconds)
        return True

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        with patch(
            "app.routes.health.db_check_database_connection",
            side_effect=slow_db_check,
        ), patch(
            "app.routes.health.watcher_util_is_watcher_running", return_value=True
        ):
            t_start = time.perf_counter()

            async def call_health():
                res = await ac.get("/health")
                t_end = time.perf_counter()
                return res, t_end - t_start

            async def call_probe():
                # Allow call_health to be scheduled and entered first
                await asyncio.sleep(0.04)
                res = await ac.get("/async-probe")
                t_end = time.perf_counter()
                return res, t_end - t_start

            (health_res, health_duration), (probe_res, probe_duration) = (
                await asyncio.gather(call_health(), call_probe())
            )

    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"
    assert probe_res.status_code == 200
    assert probe_res.json() == {"status": "probe_ok"}

    # Slow DB took at least delay_seconds (0.30s)
    assert health_duration >= delay_seconds
    # The async probe was launched after 0.04s and must finish well before
    # the 0.30s database check completes, proving the event loop was never blocked.
    assert probe_duration < delay_seconds * 0.65, (
        f"Event loop was blocked: probe took {probe_duration:.3f}s, "
        f"which was delayed by slow db ({health_duration:.3f}s)"
    )
