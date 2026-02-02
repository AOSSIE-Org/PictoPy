from platformdirs import user_data_dir
import os

# Backend Configuration
BACKEND_HOST = os.getenv('BACKEND_HOST', 'localhost')
BACKEND_PORT = int(os.getenv('BACKEND_PORT', '52123'))
PRIMARY_BACKEND_URL = os.getenv(
    'PRIMARY_BACKEND_URL',
    f'http://{BACKEND_HOST}:{BACKEND_PORT}'
)

# Sync Microservice Configuration
SYNC_MICROSERVICE_HOST = os.getenv('SYNC_MICROSERVICE_HOST', 'localhost')
SYNC_MICROSERVICE_PORT = int(os.getenv('SYNC_MICROSERVICE_PORT', '52124'))
SYNC_MICROSERVICE_URL = os.getenv(
    'SYNC_MICROSERVICE_URL',
    f'http://{SYNC_MICROSERVICE_HOST}:{SYNC_MICROSERVICE_PORT}'
)

# Model Exports Path
MODEL_EXPORTS_PATH = "app/models/ONNX_Exports"

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
# Point to the main PictoPy database
if os.getenv("GITHUB_ACTIONS") == "true":
    DATABASE_PATH = os.path.join(os.getcwd(), "test_db.sqlite3")
else:
    DATABASE_PATH = os.path.join(user_data_dir("PictoPy"), "database", "PictoPy.db")
THUMBNAIL_IMAGES_PATH = "./images/thumbnails"
IMAGES_PATH = "./images"
