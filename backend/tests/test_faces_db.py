import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from app.database.faces import db_update_face_cluster_ids_batch


class TestDbUpdateFaceClusterIdsBatch:

    def test_empty_mapping_returns_early(self):
        """Empty mapping should return without any DB calls."""
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            db_update_face_cluster_ids_batch([])
            mock_connect.assert_not_called()

    def test_sqlite_error_own_connection_rollback(self):
        """sqlite3.Error should trigger rollback and re-raise when own_connection=True."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.executemany.side_effect = sqlite3.Error("DB error")

        with patch("app.database.faces.sqlite3.connect", return_value=mock_conn), \
             patch("app.database.faces.logger") as mock_logger:

            with pytest.raises(sqlite3.Error):
                db_update_face_cluster_ids_batch(
                    [{"face_id": 1, "cluster_id": "c1"}]
                )

            mock_conn.rollback.assert_called_once()
            mock_logger.error.assert_called_once()

    def test_sqlite_error_external_cursor_no_rollback(self):
        """sqlite3.Error with external cursor should re-raise without rollback."""
        mock_cursor = MagicMock()
        mock_cursor.executemany.side_effect = sqlite3.Error("DB error")

        with patch("app.database.faces.logger") as mock_logger:
            with pytest.raises(sqlite3.Error):
                db_update_face_cluster_ids_batch(
                    [{"face_id": 1, "cluster_id": "c1"}],
                    cursor=mock_cursor
                )
            mock_logger.error.assert_called_once()
