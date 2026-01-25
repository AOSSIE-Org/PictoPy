"""
Core logging module for the PictoPy project.

This module provides centralized logging functionality for all components
of the PictoPy project, including color coding and consistent formatting.
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class ColorFormatter(logging.Formatter):
    """
    Custom formatter that adds color to log messages based on their level.
    """

    # ANSI color codes
    COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bg_black": "\033[40m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
        "bg_magenta": "\033[45m",
        "bg_cyan": "\033[46m",
        "bg_white": "\033[47m",
        "reset": "\033[0m",
    }

    def __init__(
        self,
        fmt: str,
        component_config: Dict[str, Any],
        level_colors: Dict[str, str],
        use_colors: bool = True,
    ):
        """
        Initialize the formatter with the given format string and color settings.

        Args:
            fmt: The format string to use
            component_config: Configuration for the component (prefix and color)
            level_colors: Dictionary mapping log levels to colors
            use_colors: Whether to use colors in log output
        """
        super().__init__(fmt)
        self.component_config = component_config
        self.level_colors = level_colors
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and component prefix."""
        # Add component information to the record
        component_prefix = self.component_config.get("prefix", "")
        record.component = component_prefix

        # Format the message
        formatted_message = super().format(record)

        if not self.use_colors:
            return formatted_message

        # Add color to the component prefix
        component_color = self.component_config.get("color", "")
        if component_color and component_color in self.COLORS:
            component_start = formatted_message.find(f"[{component_prefix}]")
            if component_start >= 0:
                component_end = component_start + len(f"[{component_prefix}]")
                formatted_message = (
                    formatted_message[:component_start]
                    + self.COLORS[component_color]
                    + formatted_message[component_start:component_end]
                    + self.COLORS["reset"]
                    + formatted_message[component_end:]
                )

        # Add color to the log level
        level_color = self.level_colors.get(record.levelname, "")
        if level_color:
            # Handle comma-separated color specs like "red,bg_white"
            color_codes = ""
            for color in level_color.split(","):
                if color in self.COLORS:
                    color_codes += self.COLORS[color]

            if color_codes:
                level_start = formatted_message.find(f" {record.levelname} ")
                if level_start >= 0:
                    level_end = level_start + len(f" {record.levelname} ")
                    formatted_message = (
                        formatted_message[:level_start]
                        + color_codes
                        + formatted_message[level_start:level_end]
                        + self.COLORS["reset"]
                        + formatted_message[level_end:]
                    )

        return formatted_message


def load_config() -> Dict[str, Any]:
    """
    Load the logging configuration from the JSON file.

    Returns:
        Dict containing the logging configuration
    """
    config_path = (
        Path(__file__).parent.parent.parent.parent
        / "utils"
        / "logging"
        / "logging_config.json"
    )
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading logging configuration: {e}", file=sys.stderr)
        return {}


def setup_logging(component_name: str, environment: Optional[str] = None) -> None:
    """
    Set up logging for the given component.

    Args:
        component_name: The name of the component (e.g., "backend", "sync-microservice")
        environment: The environment to use (e.g., "development", "production")
                    If None, uses the environment specified in the config or "development"
    """
    config = load_config()
    if not config:
        print(
            "No logging configuration found. Using default settings.", file=sys.stderr
        )
        return

    # Get environment settings
    if not environment:
        environment = os.environ.get(
            "ENV", config.get("default_environment", "development")
        )

    env_settings = config.get("environments", {}).get(environment, {})
    log_level = getattr(logging, env_settings.get("level", "INFO"), logging.INFO)
    use_colors = env_settings.get("colored_output", True)
    console_logging = env_settings.get("console_logging", True)

    # Get component configuration
    component_config = config.get("components", {}).get(
        component_name, {"prefix": component_name.upper(), "color": "white"}
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure specific loggers if defined in environment settings
    if "loggers" in env_settings:
        for logger_name, logger_config in env_settings["loggers"].items():
            logger = logging.getLogger(logger_name)
            if "level" in logger_config:
                logger.setLevel(getattr(logging, logger_config["level"], log_level))

    # Set up console handler
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Create formatter with component and color information
        fmt = (
            config.get("formatters", {})
            .get("default", {})
            .get("format", "[%(component)s] | %(levelname)s | %(message)s")
        )
        formatter = ColorFormatter(
            fmt, component_config, config.get("colors", {}), use_colors
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: Name of the logger, typically the module name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class InterceptHandler(logging.Handler):
    """
    Handler to intercept logs from other loggers (like Uvicorn) and redirect them
    through our custom logger.

    This implementation is based on Loguru's approach and routes logs directly to
    the root logger.
    """

    def __init__(self, component_name: str):
        """
        Initialize the InterceptHandler.

        Args:
            component_name: The name of the component (e.g., "backend")
        """
        super().__init__()
        self.component_name = component_name

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record by forwarding it through our custom logger.

        Args:
            record: The log record to process
        """
        # Get the appropriate module name
        module_name = record.name
        if "." in module_name:
            module_name = module_name.split(".")[-1]

        # Create a message that includes the original module in the format
        msg = record.getMessage()

        record.msg = f"[{module_name}] {msg}"
        record.args = ()
        # Clear exception / stack info to avoid duplicate traces
        record.exc_info = None
        record.stack_info = None

        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if handler is not self:
                handler.handle(record)


def configure_uvicorn_logging(component_name: str) -> None:
    """
    Configure Uvicorn logging to match our format.

    Args:
        component_name: The name of the component (e.g., "backend")
    """
    import logging.config

    # Create an intercept handler with our component name
    intercept_handler = InterceptHandler(component_name)

    # Make sure the handler uses our ColorFormatter
    config = load_config()
    component_config = config.get("components", {}).get(
        component_name, {"prefix": component_name.upper(), "color": "white"}
    )
    level_colors = config.get("colors", {})
    env_settings = config.get("environments", {}).get(
        os.environ.get("ENV", config.get("default_environment", "development")), {}
    )
    use_colors = env_settings.get("colored_output", True)

    fmt = "[%(component)s] | %(module)s | %(levelname)s | %(message)s"
    formatter = ColorFormatter(fmt, component_config, level_colors, use_colors)
    intercept_handler.setFormatter(formatter)

    # Configure Uvicorn loggers to use our handler
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = []  # Clear existing handlers
        uvicorn_logger.propagate = False  # Don't propagate to root
        uvicorn_logger.setLevel(logging.INFO)  # Ensure log level is at least INFO
        uvicorn_logger.addHandler(intercept_handler)

    # Also configure asyncio logger similarly
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.handlers = []
    asyncio_logger.propagate = False
    asyncio_logger.addHandler(intercept_handler)
