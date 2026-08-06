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

_server: Optional[Server] = None
_task: Optional[asyncio.Task] = None
_sock: Optional[socket.socket] = None
_port: Optional[int] = None


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


async def share_server_start() -> int:
    """Start the listener if it is not already up, and return its port."""
    global _server, _task, _sock, _port

    if _server is not None and _port is not None:
        return _port

    _sock = _bind_first_free()
    _port = _sock.getsockname()[1]

    config = Config(
        app=create_share_app(),
        log_level="warning",
        log_config=None,  # keep the backend's logging setup, as main.py does
    )
    _server = _EmbeddedServer(config)
    _task = asyncio.create_task(_server.serve(sockets=[_sock]))

    logger.info(f"Share server listening on 0.0.0.0:{_port}")
    return _port


async def share_server_stop() -> None:
    """Stop the listener. Safe to call when it was never started."""
    global _server, _task, _sock, _port

    if _server is None:
        return

    _server.should_exit = True
    if _task is not None:
        await asyncio.gather(_task, return_exceptions=True)

    # uvicorn closes the sockets it was handed, so this only matters when it
    # never got as far as serving.
    if _sock is not None:
        try:
            _sock.close()
        except OSError:
            pass

    logger.info("Share server stopped")
    _server = None
    _task = None
    _sock = None
    _port = None


def share_server_port() -> Optional[int]:
    """The live port, or None when the server is not running."""
    return _port


def share_server_is_running() -> bool:
    return _server is not None
