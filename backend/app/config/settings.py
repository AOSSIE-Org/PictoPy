from __future__ import annotations

import logging
import os
import sys
from platformdirs import user_data_dir

logger = logging.getLogger(__name__)


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


def _get_env_float(
    name: str,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            "Invalid value %r for %s (expected float); using default %s",
            raw,
            name,
            default,
        )
        return default
    if (min_value is not None and value < min_value) or (
        max_value is not None and value > max_value
    ):
        logger.warning(
            "Out-of-range value %s for %s (expected [%s, %s]); using default %s",
            value,
            name,
            min_value,
            max_value,
            default,
        )
        return default
    return value


def _get_env_int(
    name: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "Invalid value %r for %s (expected int); using default %s",
            raw,
            name,
            default,
        )
        return default
    if (min_value is not None and value < min_value) or (
        max_value is not None and value > max_value
    ):
        logger.warning(
            "Out-of-range value %s for %s (expected [%s, %s]); using default %s",
            value,
            name,
            min_value,
            max_value,
            default,
        )
        return default
    return value


# Clustering Configuration
PICTO_CLUSTERING_EPS = _get_env_float("PICTO_CLUSTERING_EPS", 0.75, min_value=0.0)
PICTO_CLUSTERING_MIN_SAMPLES = _get_env_int(
    "PICTO_CLUSTERING_MIN_SAMPLES", 2, min_value=1
)
if PICTO_CLUSTERING_MIN_SAMPLES < 2:
    logger.warning(
        f"PICTO_CLUSTERING_MIN_SAMPLES={PICTO_CLUSTERING_MIN_SAMPLES} is invalid "
        f"(minimum is 2). Resetting to 2 to prevent cluster chaining."
    )
    PICTO_CLUSTERING_MIN_SAMPLES = 2
PICTO_CLUSTERING_SIMILARITY_THRESHOLD = _get_env_float(
    "PICTO_CLUSTERING_SIMILARITY_THRESHOLD", 0.85, min_value=0.0, max_value=1.0
)
PICTO_CLUSTERING_MERGE_THRESHOLD = _get_env_float(
    "PICTO_CLUSTERING_MERGE_THRESHOLD", 0.7, min_value=0.0, max_value=1.0
)
PICTO_CLUSTERING_CONF_THRESHOLD = _get_env_float(
    "PICTO_CLUSTERING_CONF_THRESHOLD", 0.45, min_value=0.0, max_value=1.0
)
PICTO_CLUSTERING_BLUR_THRESHOLD = _get_env_float(
    "PICTO_CLUSTERING_BLUR_THRESHOLD", 80.0, min_value=0.0
)
PICTO_CLUSTERING_MIN_FACE_SIZE = _get_env_int(
    "PICTO_CLUSTERING_MIN_FACE_SIZE", 1600, min_value=1
)
