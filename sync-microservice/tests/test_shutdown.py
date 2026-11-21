import signal
from unittest.mock import AsyncMock, MagicMock, patch

from app.routes import shutdown as shutdown_module


def test_shutdown_stops_watcher_and_schedules_exit(client):
    # _delayed_shutdown is mocked so the test process is never signalled or killed.
    with patch(
        "app.routes.shutdown.watcher_util_stop_folder_watcher"
    ) as stop_watcher, patch(
        "app.routes.shutdown._delayed_shutdown", new=AsyncMock()
    ) as delayed:
        response = client.post("/shutdown")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "shutting_down"
    assert "Watcher stopped" in body["message"]
    stop_watcher.assert_called_once()
    delayed.assert_awaited_once()


def test_shutdown_still_succeeds_when_stopping_watcher_fails(client):
    with patch(
        "app.routes.shutdown.watcher_util_stop_folder_watcher",
        side_effect=RuntimeError("boom"),
    ), patch("app.routes.shutdown._delayed_shutdown", new=AsyncMock()) as delayed:
        response = client.post("/shutdown")

    assert response.status_code == 200
    assert response.json()["status"] == "shutting_down"
    delayed.assert_awaited_once()


async def test_delayed_shutdown_sends_sigterm_on_unix():
    with patch("app.routes.shutdown.platform.system", return_value="Linux"), patch(
        "app.routes.shutdown.os.getpid", return_value=1234
    ), patch("app.routes.shutdown.os.kill", new=MagicMock()) as kill, patch(
        "app.routes.shutdown.os._exit", new=MagicMock()
    ) as exit_:
        await shutdown_module._delayed_shutdown(delay=0)

    kill.assert_called_once_with(1234, signal.SIGTERM)
    exit_.assert_not_called()


async def test_delayed_shutdown_hard_exits_on_windows():
    with patch("app.routes.shutdown.platform.system", return_value="Windows"), patch(
        "app.routes.shutdown.os.kill", new=MagicMock()
    ) as kill, patch("app.routes.shutdown.os._exit", new=MagicMock()) as exit_:
        await shutdown_module._delayed_shutdown(delay=0)

    exit_.assert_called_once_with(0)
    kill.assert_not_called()
