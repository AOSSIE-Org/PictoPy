# Reference: https://medium.com/1mgofficial/how-to-override-uvicorn-logger-in-fastapi-using-loguru-124133cdcd4e

# Custom Logger Using Loguru

import logging
import sys
from pathlib import Path
from types import FrameType
from typing import Any, Dict, Optional, cast
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

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame: Optional[FrameType] = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(cls, config_path: Path) -> Any:
        print("hello logger")
        config = cls.load_logging_config(config_path)
        logging_config = config.get("logger")

        if logging_config is None:
            raise ValueError("Logger configuration not found in config file")

        path = cast(Path, logging_config.get("path"))
        level = cast(str, logging_config.get("level", "INFO"))
        retention = cast(str, logging_config.get("retention", "10 days"))
        rotation = cast(str, logging_config.get("rotation", "20 MB"))
        log_format = cast(str, logging_config.get("format", "{time} {level} {message}"))

        logger = cls.customize_logging(
            filepath=path,
            level=level,
            retention=retention,
            rotation=rotation,
            format=log_format,
        )
        return logger

    @classmethod
    def customize_logging(
        cls, filepath: Path, level: str, rotation: str, retention: str, format: str
    ) -> Any:
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
    def load_logging_config(cls, config_path: Path) -> Dict[str, Any]:
        config: Dict[str, Any] = {}
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config
