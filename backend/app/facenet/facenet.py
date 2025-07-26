from app.facecluster.init_face_cluster import get_face_cluster
import cv2
import onnxruntime
from app.config.settings import DEFAULT_FACE_DETECTION_MODEL, DEFAULT_FACENET_MODEL
from app.utils.classification import get_classes
from app.facenet.preprocess import normalize_embedding, preprocess_image
from app.yolov8.YOLOv8 import YOLOv8
from app.database.faces import insert_face_embeddings

providers = (
    ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if onnxruntime.get_device() == "GPU"
    else ["CPUExecutionProvider"]
)

session = onnxruntime.InferenceSession(DEFAULT_FACENET_MODEL, providers=providers)

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name


def get_face_embedding(image):
    """
    Generate a normalized face embedding vector from a preprocessed face image.

    Args:
        image: Preprocessed image tensor suitable for the facenet model.

    Returns:
        Normalized face embedding vector.
    """
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding)


def extract_face_embeddings(img_path):
    """
    Detect faces in the image and extract their embeddings without saving to the database.

    Uses YOLOv8 to detect faces and filters detections based on confidence scores.
    If no person is detected, returns "no_person".

    Args:
        img_path: Path to the input image.

    Returns:
        List of face embeddings or None if image fails to load.
        Returns "no_person" if no person detected in the image.
    """
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


def detect_faces(img_path):
    """
    Detect faces in an image, extract embeddings, insert them into the database,
    and add them to the global face clustering instance.

    Uses YOLOv8 with higher confidence threshold for detection.
    Adds padding around detected faces before preprocessing.

    Args:
        img_path: Path to the input image.

    Returns:
        Dictionary containing detected face class IDs, processed face tensors,
        and the number of detected faces.
    """
    yolov8_detector = YOLOv8(
        DEFAULT_FACE_DETECTION_MODEL, conf_thres=0.35, iou_thres=0.45
    )
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    boxes, scores, class_ids = yolov8_detector(img)

    processed_faces, embeddings = [], []
    for box, score in zip(boxes, scores):
        if score > 0.3:
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
        insert_face_embeddings(img_path, embeddings)
        clusters = get_face_cluster()
        for embedding in embeddings:
            clusters.add_face(embedding, img_path)

    return {
        "ids": f"{class_ids}",
        "processed_faces": processed_faces,
        "num_faces": len(embeddings),
    }
