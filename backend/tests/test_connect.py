import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from app.database.connection import get_db_connection


class TestDatabaseConnection:
    """
    Test suite for the SQLite database connection context manager.
    """

    def test_get_db_connection_returns_connection(self):
        """
        Ensure the context manager yields a valid sqlite3 connection.
        """
        with get_db_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)

    def test_commit_on_success(self):
        """
        Ensure commit is called when no exception occurs.
        """
        mock_conn = MagicMock()

        with patch("sqlite3.connect", return_value=mock_conn):
            with get_db_connection() as conn:
                assert conn == mock_conn

            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_rollback_on_exception(self):
        """
        Ensure rollback is called when an exception occurs.
        """
        mock_conn = MagicMock()

        with patch("sqlite3.connect", return_value=mock_conn):
            with pytest.raises(RuntimeError):
                with get_db_connection():
                    raise RuntimeError("Force rollback")

            mock_conn.rollback.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_pragmas_are_executed(self):
        """
        Ensure PRAGMA statements are executed when connection is created.
        """
        mock_conn = MagicMock()

        with patch("sqlite3.connect", return_value=mock_conn):
            with get_db_connection():
                pass

            expected_calls = [
                (("PRAGMA foreign_keys = ON;",),),
                (("PRAGMA ignore_check_constraints = OFF;",),),
                (("PRAGMA recursive_triggers = ON;",),),
                (("PRAGMA defer_foreign_keys = OFF;",),),
                (("PRAGMA case_sensitive_like = ON;",),),
            ]

            executed = [call.args for call in mock_conn.execute.call_args_list]

            for pragma_call in expected_calls:
                assert pragma_call[0] in executed