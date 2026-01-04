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
DATABASE_PATH = "../backend/app/database/PictoPy.db"
THUMBNAIL_IMAGES_PATH = "./images/thumbnails"
IMAGES_PATH = "./images"
