import sqlite3
import queue
import threading
from app.config.settings import DATABASE_PATH, DB_POOL_SIZE

# Thread-local storage for connections
_thread_local = threading.local()

# Connection pool as a queue
_connection_pool = None
_pool_lock = threading.Lock()

def initialize_pool(pool_size=None):
    """Initialize the connection pool with the specified size"""
    global _connection_pool
    
    if _connection_pool is not None:
        return
        
    with _pool_lock:
        if _connection_pool is None:
            size = pool_size or DB_POOL_SIZE
            _connection_pool = queue.Queue(maxsize=size)
            for _ in range(size):
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
                _connection_pool.put(conn)

def close_pool():
    """Close all connections in the pool"""
    global _connection_pool
    
    if _connection_pool is None:
        return
        
    with _pool_lock:
        if _connection_pool is not None:
            while not _connection_pool.empty():
                try:
                    conn = _connection_pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            _connection_pool = None

def get_connection():
    """Get a connection from the pool or from thread-local storage"""
    # First check if this thread already has a connection
    conn = getattr(_thread_local, 'connection', None)
    if conn is not None:
        return conn
    
    # If no connection in thread-local, get one from the pool
    if _connection_pool is None:
        raise RuntimeError("Connection pool not initialized")
    
    conn = _connection_pool.get()
    _thread_local.connection = conn
    return conn

def return_connection(conn=None):
    """Return the connection to the pool"""
    if conn is None:
        conn = getattr(_thread_local, 'connection', None)
        if conn is None:
            return
            
    # Clear thread local
    _thread_local.connection = None
    
    # Put connection back in the pool
    if _connection_pool is not None:
        _connection_pool.put(conn)

def with_connection(func):
    """Decorator to handle connection acquisition and return"""
    def wrapper(*args, **kwargs):
        conn = get_connection()
        try:
            return func(conn, *args, **kwargs)
        finally:
            return_connection(conn)
    return wrapper
