from unittest.mock import patch

import pytest


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
    client, db_ok, watcher_running, expected
):
    with patch(
        "app.routes.health.db_check_database_connection", return_value=db_ok
    ), patch(
        "app.routes.health.watcher_util_is_watcher_running",
        return_value=watcher_running,
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == expected
