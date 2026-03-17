import sqlite3
from unittest.mock import MagicMock

import pytest

from app.database import faces


def test_db_update_face_cluster_ids_batch_rolls_back_logs_and_reraises(
    monkeypatch,
):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.executemany.side_effect = sqlite3.Error("update failed")

    logger_messages = []

    def fake_connect(_):
        return mock_connection

    def fake_logger_error(message, *args):
        logger_messages.append(message % args)

    monkeypatch.setattr(faces.sqlite3, "connect", fake_connect)
    monkeypatch.setattr(faces.logger, "error", fake_logger_error)

    with pytest.raises(sqlite3.Error, match="update failed"):
        faces.db_update_face_cluster_ids_batch(
            [{"face_id": 1, "cluster_id": 2}]
        )

    mock_connection.rollback.assert_called_once()
    mock_connection.close.assert_called_once()
    assert logger_messages == ["Failed to update face cluster IDs in batch: update failed"]
