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

    # Intercepts standard logging messages and redirects them to Loguru's logger.
    # It maps standard logging levels to Loguru levels and maintains correct stack depth for tracebacks.


class CustomizeLogger:
    @classmethod
    def make_logger(cls, config_path: Path):
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

    # Creates and returns a customized logger based on the JSON config file specified by config_path.
    # Loads logging configuration and applies the settings.


    @classmethod
    def customize_logging(
        cls, filepath: Path, level: str, rotation: str, retention: str, format: str
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

    # Configures Loguru logger with handlers for stdout and file output.
    # Enables rotation and retention of log files, sets log level and format.
    # Also overrides Python's standard logging with the InterceptHandler to unify logs.


    @classmethod
    def load_logging_config(cls, config_path):
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config

    # Loads logging configuration from a JSON file at the given path.
