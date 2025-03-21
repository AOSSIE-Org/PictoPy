# Reference: https://medium.com/1mgofficial/how-to-override-uvicorn-logger-in-fastapi-using-loguru-124133cdcd4e

# Custom Logger Using Loguru

import logging
import sys
from pathlib import Path
from loguru import logger
import json
from typing import Dict, Any, Optional, Union

from app.config.settings import settings, LogConfig


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(cls, config_path: Optional[Path] = None):
        # Support both new settings-based config and legacy file-based config
        if config_path:
            # Legacy path - load from JSON file
            config = cls.load_logging_config(config_path)
            logging_config = config.get("logger")
        else:
            # New path - use Pydantic settings
            logging_config = settings.logger

        logger = cls.customize_logging(
            logging_config.path if isinstance(logging_config, LogConfig) else logging_config.get("path"),
            level=logging_config.level if isinstance(logging_config, LogConfig) else logging_config.get("level"),
            retention=logging_config.retention if isinstance(logging_config, LogConfig) else logging_config.get("retention"),
            rotation=logging_config.rotation if isinstance(logging_config, LogConfig) else logging_config.get("rotation"),
            format=logging_config.format if isinstance(logging_config, LogConfig) else logging_config.get("format"),
        )
        return logger

    @classmethod
    def customize_logging(
        cls, filepath: Union[Path, str], level: str, rotation: str, retention: str, format: str
    ):
        logger.remove()
        logger.add(
            sys.stdout, enqueue=True, backtrace=True, level=level.upper(), format=format
        )
        logger.add(
            str(filepath),
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format,
        )
        logging.basicConfig(handlers=[InterceptHandler()], level=0)

        return logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls, config_path):
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config
