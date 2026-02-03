# app/detectors/FaceDetector.py

import cv2
from app.models.FaceNet import FaceNet
from app.utils.FaceNet import FaceNet_util_preprocess_image, FaceNet_util_get_model_path
from app.utils.YOLO import YOLO_util_get_model_path
from app.models.YOLO import YOLO
from app.database.faces import db_insert_face_embeddings_by_image_id
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class FaceDetector:
    def __init__(self):
        self.yolo_detector = YOLO(
            YOLO_util_get_model_path("face"),
            conf_threshold=0.45,
            iou_threshold=0.45,
        )
        self.facenet = FaceNet(FaceNet_util_get_model_path())
        self._initialized = True
        logger.info("FaceDetector initialized with YOLO and FaceNet models.")

    def detect_faces(self, image_id: str, image_path: str, forSearch: bool = False):
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return None

        boxes, scores, class_ids = self.yolo_detector(img)
        logger.debug(f"Face detection boxes: {boxes}")
        logger.info(f"Detected {len(boxes)} faces in image {image_id}.")

        processed_faces, embeddings, bboxes, confidences = [], [], [], []

        for box, score in zip(boxes, scores):
            if score > self.yolo_detector.conf_threshold:
                x1, y1, x2, y2 = map(int, box)

                # Create bounding box dictionary in JSON format
                bbox = {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}
                bboxes.append(bbox)
                confidences.append(float(score))

                padding = 20
                face_img = img[
                    max(0, y1 - padding) : min(img.shape[0], y2 + padding),
                    max(0, x1 - padding) : min(img.shape[1], x2 + padding),
                ]
                processed_face = FaceNet_util_preprocess_image(face_img)
                processed_faces.append(processed_face)

                embedding = self.facenet.get_embedding(processed_face)
                embeddings.append(embedding)

        if not forSearch and embeddings:
            db_insert_face_embeddings_by_image_id(
                image_id, embeddings, confidence=confidences, bbox=bboxes
            )

        return {
            "ids": f"{class_ids}",
            "processed_faces": processed_faces,
            "num_faces": len(embeddings),
        }

    def close(self):
        """
        Close the resources held by the FaceDetector.
        """
        if self.yolo_detector is not None:
            self.yolo_detector.close()
            self.yolo_detector = None

        if self.facenet is not None:
            self.facenet.close()
            self.facenet = None
