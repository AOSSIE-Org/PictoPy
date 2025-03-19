from app.facecluster.init_face_cluster import get_face_cluster
import cv2
import onnxruntime
from app.config.settings import DEFAULT_FACE_DETECTION_MODEL, DEFAULT_FACENET_MODEL
from app.utils.classification import get_classes
from app.facenet.preprocess import normalize_embedding, preprocess_image
from app.yolov8.YOLOv8 import YOLOv8
from app.database.faces import insert_face_embeddings
from typing import Optional
from app.utils.progress import ProgressTracker

providers = (
    ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if onnxruntime.get_device() == "GPU"
    else ["CPUExecutionProvider"]
)

session = onnxruntime.InferenceSession(DEFAULT_FACENET_MODEL, providers=providers)

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name


def get_face_embedding(image):
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding)


def extract_face_embeddings(img_path):
    # Return face embeddings from the image but do not add them to the db.
    yolov8_detector = YOLOv8(
        DEFAULT_FACE_DETECTION_MODEL, conf_thres=0.2, iou_thres=0.3
    )

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    # If "person" `class_id` is not found in the image, return early
    class_ids = get_classes(img_path)
    if not class_ids or "0" not in class_ids.split(","):
        print(f"No person detected in image: {img_path}")
        return "no_person"

    boxes, scores, class_ids = yolov8_detector(img)

    embeddings = []
    for box, score in zip(boxes, scores):
        if score > 0.5:
            x1, y1, x2, y2 = map(int, box)
            face_img = img[y1:y2, x1:x2]
            processed_face = preprocess_image(face_img)
            embedding = get_face_embedding(processed_face)
            embeddings.append(embedding)

    return embeddings


def detect_faces(img_path: str, progress_tracker: Optional[ProgressTracker] = None):
    """Modified to support progress tracking"""
    yolov8_detector = YOLOv8(
        DEFAULT_FACE_DETECTION_MODEL, conf_thres=0.2, iou_thres=0.3
    )

    if progress_tracker:
        progress_tracker.update(status="Loading image")

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    if progress_tracker:
        progress_tracker.update(status="Detecting faces")

    boxes, scores, class_ids = yolov8_detector(img)

    processed_faces, embeddings = [], []
    for box, score in zip(boxes, scores):
        if score > 0.5:
            if progress_tracker:
                progress_tracker.update(status="Processing face")

            x1, y1, x2, y2 = map(int, box)
            face_img = img[y1:y2, x1:x2]
            padding = 20
            h, w = face_img.shape[:2]
            face_img = img[
                max(0, y1 - padding) : min(img.shape[0], y2 + padding),
                max(0, x1 - padding) : min(img.shape[1], x2 + padding),
            ]
            processed_face = preprocess_image(face_img)
            processed_faces.append(processed_face)
            embedding = get_face_embedding(processed_face)
            embeddings.append(embedding)

    if embeddings:
        if progress_tracker:
            progress_tracker.update(status="Saving embeddings")

        insert_face_embeddings(img_path, embeddings)
        clusters = get_face_cluster()
        for embedding in embeddings:
            clusters.add_face(embedding, img_path)

    return {
        "ids": f"{class_ids}",
        "processed_faces": processed_faces,
        "num_faces": len(embeddings),
    }
