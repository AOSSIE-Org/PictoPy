# Model Exports Path
MODEL_EXPORTS_PATH = "app/models/ONNX_Exports"

# Microservice URLs
SYNC_MICROSERVICE_URL = "http://localhost:8001/api/v1"

# =============================================================================
# OBJECT DETECTION MODELS
# =============================================================================

# YOLO models for general object detection
# Different sizes offer trade-offs between speed and accuracy
SMALL_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Small.onnx"    # Fast, moderate accuracy
NANO_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Nano.onnx"      # Fastest, lower accuracy
MEDIUM_OBJ_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Medium.onnx"  # Slower, higher accuracy

# =============================================================================
# FACE DETECTION MODELS
# =============================================================================

# YOLO models specifically trained for face detection
# Optimized for detecting human faces in images
SMALL_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Small_Face.onnx"    # Fast face detection
NANO_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Nano_Face.onnx"      # Fastest face detection
MEDIUM_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Medium_Face.onnx"  # Most accurate face detection

# Face Detection Models:
SMALL_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Small_Face.onnx"
NANO_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Nano_Face.onnx"
MEDIUM_FACE_DETECTION_MODEL = f"{MODEL_EXPORTS_PATH}/YOLOv11_Medium_Face.onnx"

# FaceNet model for extracting face embeddings (128-dimensional vectors)
# Used for face clustering and recognition
DEFAULT_FACENET_MODEL = f"{MODEL_EXPORTS_PATH}/FaceNet_128D.onnx"

# =============================================================================
# FILE SYSTEM PATHS
# =============================================================================

# Test environment paths
TEST_INPUT_PATH = "tests/inputs"      # Directory containing test input files
TEST_OUTPUT_PATH = "tests/outputs"    # Directory for test output files

# Database configuration
DATABASE_PATH = "app/database/PictoPy.db"  # SQLite database file location

# Image storage paths
THUMBNAIL_IMAGES_PATH = "./images/thumbnails"  # Directory for image thumbnails
IMAGES_PATH = "./images"                        # Main directory for image storage
