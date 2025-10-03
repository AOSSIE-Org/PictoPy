"""
__init__.py for the backend.app.logging package.

This file allows the package to be imported and initializes logging.
"""

from .setup_logging import get_logger, configure_uvicorn_logging, setup_logging

__all__ = ["get_logger", "configure_uvicorn_logging", "setup_logging"]
