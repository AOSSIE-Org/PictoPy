"""
Thread-safe SQLite connection management for FastAPI backend.

This module provides thread-safe database connection handling using:
1. threading.local() for per-thread connection storage
2. Context managers for automatic resource cleanup
3. Connection pooling with proper isolation

SQLite's threading model requires each thread to have its own connection
to avoid race conditions and data corruption during concurrent operations.
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Optional
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Thread-local storage for database connections
_thread_local = threading.local()

# Lock for write operations to serialize database writes
_write_lock = threading.Lock()


class DatabaseConnectionManager:
    """
    Thread-safe SQLite connection manager.
    
    Provides per-thread connections with proper lifecycle management.
    Each thread gets its own connection to avoid SQLite threading issues.
    """
    
    def __init__(self, database_path: str = DATABASE_PATH):
        self.database_path = database_path
        self._local = threading.local()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create a connection for the current thread.
        
        Returns:
            sqlite3.Connection: Thread-local database connection
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self._create_connection()
            logger.debug(f"Created new connection for thread {threading.current_thread().name}")
        return self._local.connection
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new SQLite connection with proper configuration.
        
        Returns:
            sqlite3.Connection: Configured database connection
        """
        conn = sqlite3.connect(
            self.database_path,
            timeout=30.0,  # Wait up to 30 seconds for locks
            isolation_level=None,  # Autocommit mode, we handle transactions manually
        )
        
        # Enable WAL mode for better concurrent read performance
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # Enforce all integrity constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA ignore_check_constraints = OFF;")
        conn.execute("PRAGMA recursive_triggers = ON;")
        conn.execute("PRAGMA defer_foreign_keys = OFF;")
        conn.execute("PRAGMA case_sensitive_like = ON;")
        
        # Optimize for concurrent access
        conn.execute("PRAGMA busy_timeout = 30000;")  # 30 second busy timeout
        conn.execute("PRAGMA synchronous = NORMAL;")  # Balance safety and speed
        
        return conn
    
    def close_connection(self) -> None:
        """Close the connection for the current thread if it exists."""
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            try:
                self._local.connection.close()
                logger.debug(f"Closed connection for thread {threading.current_thread().name}")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._local.connection = None
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for getting a thread-safe database connection.
        
        The connection is reused within the same thread but properly
        isolated between different threads.
        
        Yields:
            sqlite3.Connection: Thread-local database connection
        """
        conn = self._get_connection()
        try:
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions with automatic commit/rollback.
        
        Provides:
        - Automatic transaction begin
        - Commit on success
        - Rollback on failure
        - Thread-safe connection handling
        
        Yields:
            sqlite3.Connection: Thread-local database connection within a transaction
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")  # Acquire write lock immediately
            yield conn
            conn.execute("COMMIT")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
    
    @contextmanager
    def write_transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for serialized write operations.
        
        Uses a global lock to ensure only one write operation happens at a time,
        preventing database lock contention issues.
        
        Yields:
            sqlite3.Connection: Thread-local database connection with write lock
        """
        with _write_lock:
            with self.transaction() as conn:
                yield conn


# Global connection manager instance
_connection_manager = DatabaseConnectionManager()


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Get a thread-safe database connection.
    
    This is the primary interface for obtaining database connections.
    Each thread gets its own connection, ensuring thread safety.
    
    Yields:
        sqlite3.Connection: Thread-local database connection
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM images")
            results = cursor.fetchall()
    """
    with _connection_manager.get_connection() as conn:
        yield conn


@contextmanager
def get_db_transaction() -> Generator[sqlite3.Connection, None, None]:
    """
    Get a database connection with automatic transaction management.
    
    Automatically commits on success or rolls back on failure.
    
    Yields:
        sqlite3.Connection: Thread-local database connection in a transaction
        
    Example:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO images ...")
            cursor.execute("INSERT INTO image_classes ...")
            # Automatically committed if no exception
    """
    with _connection_manager.transaction() as conn:
        yield conn


@contextmanager
def get_db_write_transaction() -> Generator[sqlite3.Connection, None, None]:
    """
    Get a serialized write transaction.
    
    Use this for write operations that need to be serialized across threads
    to prevent lock contention.
    
    Yields:
        sqlite3.Connection: Thread-local database connection with write lock
        
    Example:
        with get_db_write_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE images SET ...")
            # Write lock released after context exits
    """
    with _connection_manager.write_transaction() as conn:
        yield conn


def close_thread_connection() -> None:
    """
    Close the database connection for the current thread.
    
    Call this when a thread is about to terminate to clean up resources.
    """
    _connection_manager.close_connection()


def get_new_connection() -> sqlite3.Connection:
    """
    Create a new standalone database connection.
    
    Use this only when you need a connection outside of the thread-local
    management system (e.g., for background tasks or process pools).
    
    The caller is responsible for closing this connection.
    
    Returns:
        sqlite3.Connection: New database connection
    """
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=30.0,
    )
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn
