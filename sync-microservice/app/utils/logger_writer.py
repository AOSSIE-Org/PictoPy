"""
Logger Writer utility for redirecting stdout/stderr to logging system.

This module provides a custom writer class that can redirect standard output
and error streams to the logging system, ensuring all output goes through
the centralized logging configuration.
"""

import logging


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

    def write(self, message: str) -> None:
        """
        Write a message to the logger.

        Args:
            message: The message to write
        """
        # Buffer the message until we get a complete line
        self.buffer += message
        if message.endswith("\n"):
            # Log the complete line (minus the newline)
            line = self.buffer.rstrip("\n")
            if line:  # Only log non-empty lines
                self.logger.log(self.level, line)
            self.buffer = ""

    def flush(self) -> None:
        """Flush any remaining buffer content."""
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ""
