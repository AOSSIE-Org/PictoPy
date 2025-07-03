from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any
from pathlib import Path
import os

class LogConfig(BaseSettings):
    """Logging configuration"""
    path: str = "logs/app.log"
    level: str = "INFO"
    rotation: str = "20 MB"
    retention: str = "1 month"
    format: str = "{time} | {level} | {message}"

# Set paths
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = str(APP_DIR.parent / "pictopy.db")
THUMBNAIL_IMAGES_PATH = str(APP_DIR.parent / "images")

# Model paths
DEFAULT_FACE_DETECTION_MODEL = "models/face_detection.onnx"
DEFAULT_OBJ_DETECTION_MODEL = "models/yolov8n.onnx"
DEFAULT_FACENET_MODEL = "models/facenet.onnx"

class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "PictoPy"
    debug: bool = True
    logger: LogConfig = LogConfig()
    database_path: str = DATABASE_PATH
    thumbnail_path: str = THUMBNAIL_IMAGES_PATH

settings = Settings()
