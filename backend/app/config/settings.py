import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Database paths
DATABASE_PATH = DATA_DIR / "database.db"
FACES_DATABASE_PATH = DATA_DIR / "faces.db"
IMAGES_DATABASE_PATH = DATA_DIR / "images.db"
ALBUM_DATABASE_PATH = DATA_DIR / "albums.db"
MAPPINGS_DATABASE_PATH = DATA_DIR / "mappings.db"
CLUSTERS_DATABASE_PATH = DATA_DIR / "clusters.db"

# Create data directory if it doesn't exist
for db_path in [DATABASE_PATH, FACES_DATABASE_PATH, IMAGES_DATABASE_PATH, 
                ALBUM_DATABASE_PATH, MAPPINGS_DATABASE_PATH, CLUSTERS_DATABASE_PATH]:
    os.makedirs(db_path.parent, exist_ok=True)

# Model paths
DEFAULT_FACE_DETECTION_MODEL = "app/models/yolov8n-face.onnx"
DEFAULT_FACENET_MODEL = "app/models/facenet.onnx"
DEFAULT_OBJ_DETECTION_MODEL = "app/models/yolov8n.onnx"

# Test paths
TEST_INPUT_PATH = "tests/inputs"
TEST_OUTPUT_PATH = "tests/outputs"

# Images and thumbnails paths
IMAGES_PATH = DATA_DIR / "images"
THUMBNAIL_IMAGES_PATH = "./images"

# Ensure images directory exists
os.makedirs(IMAGES_PATH, exist_ok=True)
os.makedirs(THUMBNAIL_IMAGES_PATH, exist_ok=True)


