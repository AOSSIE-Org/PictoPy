"""
Logger Writer utility for redirecting stdout/stderr to logging system.

This module provides a custom writer class that can redirect standard output
and error streams to the logging system, ensuring all output goes through
the centralized logging configuration.
"""

import logging
import sys
from contextlib import contextmanager
from typing import Generator


class LoggerWriter:
    """Custom writer that redirects stdout/stderr to logger."""

    def __init__(self, logger: logging.Logger, level: int):
        """
        Initialize the LoggerWriter.

        Args:
            logger: The logger instance to write to
            level: The logging level to use (e.g., logging.INFO, logging.ERROR)
        """
        self.logger = logger
        self.level = level
        self.buffer = ""
        self._in_write = False  # Recursion guard

    def write(self, message: str) -> None:
        """
        Write a message to the logger.

        Args:
            message: The message to write
        """
        # Prevent infinite recursion if logging tries to write to stdout/stderr
        if self._in_write:
            return

        self._in_write = True
        try:
            # Buffer the message until we get a complete line
            self.buffer += message
            if message.endswith("\n"):
                # Log the complete line (minus the newline)
                line = self.buffer.rstrip("\n")
                if line:  # Only log non-empty lines
                    self.logger.log(self.level, line)
                self.buffer = ""
        finally:
            self._in_write = False

    def flush(self) -> None:
        """Flush any remaining buffer content."""
        # Prevent infinite recursion if logging tries to write to stdout/stderr
        if self._in_write:
            return

        self._in_write = True
        try:
            if self.buffer:
                self.logger.log(self.level, self.buffer)
                self.buffer = ""
        finally:
            self._in_write = False


@contextmanager
def redirect_stdout_stderr(
    logger: logging.Logger,
    stdout_level: int = logging.INFO,
    stderr_level: int = logging.ERROR,
) -> Generator[None, None, None]:
    """
    Context manager for safely redirecting stdout/stderr to logger.

    This provides a safer alternative to global redirection.

    Args:
        logger: The logger instance to write to
        stdout_level: Logging level for stdout messages
        stderr_level: Logging level for stderr messages

    Example:
        with redirect_stdout_stderr(logger):
            print("This will be logged instead of printed")
    """
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        sys.stdout = LoggerWriter(logger, stdout_level)
        sys.stderr = LoggerWriter(logger, stderr_level)
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
