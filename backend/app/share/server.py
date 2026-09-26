"""
Starting and stopping the share listener.

Runs as an asyncio task on the backend's own event loop rather than in a thread
or a separate process, so quitting PictoPy takes the share server with it and
the in-memory registry cannot outlive the app.
"""

from __future__ import annotations

import asyncio
import socket
import sys
from typing import List, Optional

from uvicorn import Config, Server

from app.config.settings import SHARE_SERVER_PORT
from app.logging.setup_logging import get_logger
from app.share.app import create_share_app

logger = get_logger(__name__)

# How many ports past the preferred one to try before giving up. Windows
# firewall rules are per-binary, so a different port needs no new permission.
_PORT_ATTEMPTS = 5

# Long enough for an in-flight photo to finish, short enough that quitting the
# app never appears to hang on a recipient who left a download open.
_STOP_TIMEOUT = 5.0

_server: Optional[Server] = None
_task: Optional[asyncio.Task] = None
_sock: Optional[socket.socket] = None
_port: Optional[int] = None

# Serialises start against stop. Without it a revoke that decides to stop can
# interleave with a create that decides the listener is already up, and the
# new share is left pointing at a socket that is closing.
_lifecycle_lock = asyncio.Lock()


class _EmbeddedServer(Server):
    """
    A uvicorn server that leaves the process's signal handling alone.

    The default implementation installs its own SIGINT/SIGTERM handlers when
    started on the main thread, which would take them away from the backend
    that is hosting us.
    """

    def install_signal_handlers(self) -> None:
        return None


def _bind(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR means something different on Windows: it lets a second
    # socket bind a port that is already taken, so a clash would look like a
    # success and the share would silently serve nothing.
    if sys.platform != "win32":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
    except OSError:
        sock.close()
        raise
    return sock


def _bind_first_free() -> socket.socket:
    """
    Bind ahead of uvicorn rather than letting it bind on startup.

    uvicorn raises SystemExit when it cannot bind, which would terminate the
    whole backend instead of failing one share.
    """
    errors: List[str] = []
    for offset in range(_PORT_ATTEMPTS):
        port = SHARE_SERVER_PORT + offset
        try:
            return _bind(port)
        except OSError as error:
            errors.append(f"{port}: {error}")
    raise OSError("Could not bind a share port — tried " + "; ".join(errors))


def _clear() -> None:
    """Drop all listener state, closing the socket if uvicorn never took it."""
    global _server, _task, _sock, _port
    if _sock is not None:
        try:
            _sock.close()
        except OSError:
            pass
    _server = None
    _task = None
    _sock = None
    _port = None


def _on_serve_done(task: asyncio.Task) -> None:
    """
    Notice a listener that died on its own.

    Without this the task's exception is never retrieved, and worse, `_port`
    would stay set so the next create would hand out a URL for a socket that
    stopped accepting connections.
    """
    if task is not _task:
        return  # already superseded by a newer listener
    if not task.cancelled():
        error = task.exception()
        if error is not None:
            logger.error(f"Share server stopped unexpectedly: {error}")
    _clear()


async def share_server_start() -> int:
    """Start the listener if it is not already up, and return its port."""
    global _server, _task, _sock, _port

    async with _lifecycle_lock:
        if _port is not None and _task is not None and not _task.done():
            return _port
        if _server is not None:
            # A previous listener died; drop it before binding again.
            _clear()

        _sock = _bind_first_free()
        _port = _sock.getsockname()[1]

        config = Config(
            app=create_share_app(),
            log_level="warning",
            log_config=None,  # keep the backend's logging setup, as main.py does
            timeout_graceful_shutdown=_STOP_TIMEOUT,
        )
        _server = _EmbeddedServer(config)
        _task = asyncio.create_task(_server.serve(sockets=[_sock]))
        _task.add_done_callback(_on_serve_done)

        logger.info(f"Share server listening on 0.0.0.0:{_port}")
        return _port


async def share_server_stop() -> None:
    """Stop the listener. Safe to call when it was never started."""
    async with _lifecycle_lock:
        server, task = _server, _task
        if server is None:
            return

        server.should_exit = True
        if task is not None and not task.done():
            try:
                await asyncio.wait_for(task, timeout=_STOP_TIMEOUT)
            except asyncio.TimeoutError:
                # wait_for has already cancelled it; a recipient holding a
                # long download must not keep the port open indefinitely.
                logger.warning("Share server did not stop in time; cancelled it")
            except Exception:
                pass  # the done callback logged whatever serve() raised

        _clear()
        logger.info("Share server stopped")


def share_server_port() -> Optional[int]:
    """The live port, or None when the server is not running."""
    return _port


def share_server_is_running() -> bool:
    return _port is not None and _task is not None and not _task.done()
