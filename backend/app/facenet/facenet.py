from numpy import shape
import cv2
import onnxruntime
from app.config.settings import DEFAULT_FACE_DETECTION_MODEL, DEFAULT_FACENET_MODEL
from app.facenet.preprocess import normalize_embedding, preprocess_image
from app.yolov8.YOLOv8 import YOLOv8
from app.database.faces import db_insert_face_embeddings_by_image_id

providers = (
    ["CUDAExecutionProvider", "CPUExecutionProvider"] if onnxruntime.get_device() == "GPU" else ["CPUExecutionProvider"]
)

session = onnxruntime.InferenceSession(DEFAULT_FACENET_MODEL, providers=providers)

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name


def get_face_embedding(image):
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding)


def detect_faces(image_id, image_path):
    yolov8_detector = YOLOv8(DEFAULT_FACE_DETECTION_MODEL, conf_thres=0.35, iou_thres=0.45)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {image_path}")
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

    print(type(embeddings))
    if embeddings:
        db_insert_face_embeddings_by_image_id(image_id, embeddings)
        # clusters = get_face_cluster()
        # for embedding in embeddings:
        #     clusters.add_face(embedding, img_path)

    return {
        "ids": f"{class_ids}",
        "processed_faces": processed_faces,
        "num_faces": len(embeddings),
    }
