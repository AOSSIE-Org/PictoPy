import os
import sys

from platformdirs import user_data_dir

if getattr(sys, "frozen", False):
    MODEL_EXPORTS_PATH = os.path.join(user_data_dir("PictoPy"), "models")
else:
    MODEL_EXPORTS_PATH = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "models", "ONNX_Exports")
    )

# Microservice URLs
SYNC_MICROSERVICE_URL = "http://localhost:52124"

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
if os.getenv("GITHUB_ACTIONS") == "true":
    DATABASE_PATH = os.path.join(os.getcwd(), "test_db.sqlite3")
else:
    DATABASE_PATH = os.path.join(user_data_dir("PictoPy"), "database", "PictoPy.db")
THUMBNAIL_IMAGES_PATH = os.path.join(user_data_dir("PictoPy"), "thumbnails")
IMAGES_PATH = "./images"

# Clustering Configuration
PICTO_CLUSTERING_EPS = float(os.getenv("PICTO_CLUSTERING_EPS", "0.75"))
PICTO_CLUSTERING_MIN_SAMPLES = int(os.getenv("PICTO_CLUSTERING_MIN_SAMPLES", "2"))
PICTO_CLUSTERING_SIMILARITY_THRESHOLD = float(
    os.getenv("PICTO_CLUSTERING_SIMILARITY_THRESHOLD", "0.85")
)
PICTO_CLUSTERING_MERGE_THRESHOLD = float(
    os.getenv("PICTO_CLUSTERING_MERGE_THRESHOLD", "0.7")
)
PICTO_CLUSTERING_CONF_THRESHOLD = float(
    os.getenv("PICTO_CLUSTERING_CONF_THRESHOLD", "0.45")
)
PICTO_CLUSTERING_BLUR_THRESHOLD = float(
    os.getenv("PICTO_CLUSTERING_BLUR_THRESHOLD", "80.0")
)
PICTO_CLUSTERING_MIN_FACE_SIZE = int(
    os.getenv("PICTO_CLUSTERING_MIN_FACE_SIZE", "1600")
)
