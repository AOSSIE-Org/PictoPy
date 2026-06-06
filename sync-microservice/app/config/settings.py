import os
import secrets
import tempfile
import time as _time
import warnings

from platformdirs import user_data_dir

# Model Exports Path
MODEL_EXPORTS_PATH = "app/models/ONNX_Exports"
PRIMARY_BACKEND_URL = "http://localhost:52123"
SYNC_MICROSERVICE_URL = "http://localhost:52124"

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

# The backend writes a fresh cryptographic token to this temp file on every
# startup.  The sync microservice reads the same file so both services share
# a single token without any additional coordination.
SHUTDOWN_TOKEN_FILE: str = os.path.join(tempfile.gettempdir(), "pictopy_shutdown.token")

# Retry for up to 5 seconds to handle the race where the sync microservice
# starts before the backend has had a chance to write the token file.
_deadline = _time.monotonic() + 5.0
SHUTDOWN_TOKEN: str = ""
while _time.monotonic() < _deadline:
    try:
        with open(SHUTDOWN_TOKEN_FILE) as _f:
            _token = _f.read().strip()
        if _token:
            SHUTDOWN_TOKEN = _token
            break
    except FileNotFoundError:
        pass
    _time.sleep(0.1)

if not SHUTDOWN_TOKEN:
    # Backend token unavailable after timeout — generate a fallback so the
    # service can still start, but log a clear warning so the issue is visible.
    SHUTDOWN_TOKEN = secrets.token_hex(32)
    warnings.warn(
        "pictopy_shutdown.token not found after 5 s; using an independent "
        "shutdown token. The sync /shutdown endpoint may reject requests from "
        "the Tauri frontend. Ensure the backend starts before the sync service.",
        RuntimeWarning,
        stacklevel=1,
    )
