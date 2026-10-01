import httpx
import pytest
from unittest.mock import patch, MagicMock

from app.utils.API import API_util_restart_sync_microservice_watcher


class TestApiUtilsWatcher:
    @patch("app.utils.API.httpx.post")
    def test_restart_sync_microservice_watcher_success(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = API_util_restart_sync_microservice_watcher()
        assert result is True
        mock_post.assert_called_once()

    @patch("app.utils.API.httpx.post")
    def test_restart_sync_microservice_watcher_failure_status(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = API_util_restart_sync_microservice_watcher()
        assert result is False
        mock_post.assert_called_once()

    @patch("app.utils.API.httpx.post")
    def test_restart_sync_microservice_watcher_request_error(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        result = API_util_restart_sync_microservice_watcher()
        assert result is False
        mock_post.assert_called_once()

    @patch("app.utils.API.httpx.post")
    def test_restart_sync_microservice_watcher_unexpected_error(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = RuntimeError("Unexpected internal crash")

        result = API_util_restart_sync_microservice_watcher()
        assert result is False
        mock_post.assert_called_once()
