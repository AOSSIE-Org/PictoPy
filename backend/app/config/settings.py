import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
API_KEY = os.getenv("API_KEY", "dev-api-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS Settings
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:1420,tauri://localhost"
).split(",")

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

# Model Exports Path
MODEL_EXPORTS_PATH = "app/models/ONNX_Exports"

# Microservice URLs
SYNC_MICROSERVICE_URL = os.getenv(
    "SYNC_MICROSERVICE_URL", "http://localhost:8001/api/v1"
)

CONFIDENCE_PERCENT = 0.6
# Object Detection Models:
SMALL_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Small.onnx"
NANO_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Nano.onnx"
MEDIUM_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Medium.onnx"

# Face Detection Models:
SMALL_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Small_Face.onnx"
NANO_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Nano_Face.onnx"
MEDIUM_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Medium_Face.onnx"

# FaceNet Model to extract face embeddings:
DEFAULT_FACENET_MODEL = f"{MODEL_EXPORTS_PATH}/FaceNet_128D.onnx"

TEST_INPUT_PATH = "tests/inputs"
TEST_OUTPUT_PATH = "tests/outputs"
DATABASE_PATH = os.getenv("DATABASE_PATH", "app/database/PictoPy.db")
THUMBNAIL_IMAGES_PATH = "./images/thumbnails"
IMAGES_PATH = "./images"
