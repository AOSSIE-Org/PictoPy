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
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
DATABASE_PATH = str(APP_DIR / "pictopy.db")
THUMBNAIL_IMAGES_PATH = str(APP_DIR / "images")

# Model paths
DEFAULT_FACE_DETECTION_MODEL = str(APP_DIR / "models/face_detection.onnx")
DEFAULT_OBJ_DETECTION_MODEL = str(APP_DIR / "models/yolov8n.onnx")
DEFAULT_FACENET_MODEL = str(APP_DIR / "models/facenet.onnx")

class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "PictoPy"
    debug: bool = True
    logger: LogConfig = LogConfig()
    database_path: str = DATABASE_PATH
    thumbnail_path: str = THUMBNAIL_IMAGES_PATH

settings = Settings()


TEST_INPUT_PATH = "tests/inputs"
TEST_OUTPUT_PATH = "tests/outputs"
DATABASE_PATH = "app/database/PictoPy.db"
THUMBNAIL_IMAGES_PATH = "./images"
IMAGES_PATH = "./images"

