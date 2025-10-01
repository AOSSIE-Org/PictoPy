"""
Core logging module for the PictoPy project using Loguru.

This module provides centralized logging functionality for all components
of the PictoPy project using the Loguru library.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger


def load_config() -> Dict[str, Any]:
    """
    Load the logging configuration from the JSON file.
    
    Returns:
        Dict containing the logging configuration
    """
    config_path = Path(__file__).parent / "logging_config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading logging configuration: {e}", file=sys.stderr)
        return {}


def setup_logging(component_name: str, environment: Optional[str] = None) -> None:
    """
    Set up logging for the given component using Loguru.
    
    Args:
        component_name: The name of the component (e.g., "backend", "sync-microservice")
        environment: The environment to use (e.g., "development", "production")
                    If None, uses the environment specified in the config or "development"
    """
    config = load_config()
    if not config:
        print("No logging configuration found. Using default settings.", file=sys.stderr)
        return

    # Get environment settings
    if not environment:
        environment = os.environ.get("ENV", config.get("default_environment", "development"))
    
    env_settings = config.get("environments", {}).get(environment, {})
    log_level = env_settings.get("level", "INFO")
    use_colors = env_settings.get("colored_output", True)
    console_logging = env_settings.get("console_logging", True)
    
    # Get component configuration
    component_config = config.get("components", {}).get(
        component_name, {"prefix": component_name.upper(), "color": "white"}
    )
    component_prefix = component_config.get("prefix", component_name.upper())
    
    # Remove default loguru handler
    logger.remove()
    
    # Format based on configuration
    log_format = "<level>{level: <8}</level> | "
    
    # Add component prefix with its color
    component_color = component_config.get("color", "white")
    if use_colors:
        log_format += f"<{component_color}>[{component_prefix}]</{component_color}> | "
    else:
        log_format += f"[{component_prefix}] | "
    
    log_format += "{name} | {message}"
    
    # Add console handler
    if console_logging:
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=use_colors,
        )


def get_logger(name: str):
    """
    Get a logger with the given name.
    
    Args:
        name: Name of the logger, typically the module name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


def configure_uvicorn_logging(component_name: str) -> None:
    """
    Configure Uvicorn logging to use our Loguru setup.
    
    Args:
        component_name: The name of the component (e.g., "backend")
    """
    # Intercept uvicorn's default logging
    import logging
    
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Configure standard logging to use our Loguru handler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Replace logging handlers with Loguru for all uvicorn loggers
    for name in logging.root.manager.loggerDict.keys():
        if name.startswith("uvicorn."):
            logging.getLogger(name).handlers = []