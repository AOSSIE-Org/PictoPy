import asyncio
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch

import httpx
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
    client: TestClient, db_ok: bool, watcher_running: bool, expected: dict[str, str]
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
    it inside a worker thread (run_in_threadpool), leaving the asyncio event
    loop free to service concurrent requests without blocking.
    """
    app = FastAPI()
    app.include_router(health.router)

    # An async endpoint that must execute immediately if the event loop is free
    @app.get("/async-probe")
    async def async_probe() -> dict[str, str]:
        return {"status": "probe_ok"}

    db_started = threading.Event()
    probe_completed = threading.Event()

    def slow_db_check() -> bool:
        db_started.set()
        # Hold the database check until the async probe completes
        if not probe_completed.wait(timeout=5.0):
            raise TimeoutError(
                "probe_completed was not set before database check timed out"
            )
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

            async def call_health() -> tuple[httpx.Response, float]:
                res = await ac.get("/health")
                t_end = time.perf_counter()
                return res, t_end - t_start

            async def call_probe() -> tuple[httpx.Response, float]:
                # Wait until slow_db_check has started executing
                loop = asyncio.get_running_loop()
                deadline = loop.time() + 5.0
                while not db_started.is_set():
                    if health_task.done() and health_task.exception() is not None:
                        raise RuntimeError(
                            "Health check task failed before database check started"
                        ) from health_task.exception()
                    if loop.time() > deadline:
                        raise TimeoutError(
                            "Database check did not start within timeout"
                        )
                    await asyncio.sleep(0.005)

                try:
                    res = await ac.get("/async-probe")
                finally:
                    probe_completed.set()
                t_end = time.perf_counter()
                return res, t_end - t_start

            health_task = asyncio.create_task(call_health())
            probe_task = asyncio.create_task(call_probe())

            try:
                (health_res, health_duration), (probe_res, probe_duration) = (
                    await asyncio.gather(health_task, probe_task)
                )
            finally:
                # Ensure the worker thread is always released even if the test fails
                probe_completed.set()

    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"
    assert probe_res.status_code == 200
    assert probe_res.json() == {"status": "probe_ok"}

    # Confirm that probe completed while slow_db_check was active
    assert probe_completed.is_set()
    assert probe_duration < health_duration
