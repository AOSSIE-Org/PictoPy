# Reference: https://medium.com/1mgofficial/how-to-override-uvicorn-logger-in-fastapi-using-loguru-124133cdcd4e

# Custom Logger Using Loguru

import logging
import sys
from pathlib import Path
from loguru import logger
import json


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
        # Intercepts logs from standard logging and redirects them to loguru logger
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            # Map logging level numbers to loguru level names if not found
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        # Find the caller frame outside logging module for correct log origin
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Bind extra context and log the message with exception info if any
        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(cls, config_path: Path):
        # Reads logger config from JSON file and initializes loguru logger accordingly
        print("hello logger")
        config = cls.load_logging_config(config_path)
        logging_config = config.get("logger")

        logger = cls.customize_logging(
            logging_config.get("path"),
            level=logging_config.get("level"),
            retention=logging_config.get("retention"),
            rotation=logging_config.get("rotation"),
            format=logging_config.get("format"),
        )
        return logger

    @classmethod
    def customize_logging(
        cls, filepath: Path, level: str, rotation: str, retention: str, format: str
    ):
        # Sets up loguru logger:
        # - Removes default handlers
        # - Adds stdout and file handlers with rotation and retention policies
        # - Configures Python's standard logging to be intercepted by loguru via InterceptHandler
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

        # Returns logger instance with optional bound context fields
        return logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls, config_path):
        # Loads logger configuration JSON from the given file path and returns it as dict
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config
