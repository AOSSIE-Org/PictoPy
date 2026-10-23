# app/detectors/FaceDetector.py

from typing import Dict, List, Optional, TypedDict

import cv2
import numpy as np
from app.models.FaceNet import FaceNet
from app.utils.FaceNet import FaceNet_util_preprocess_image, FaceNet_util_get_model_path
from app.utils.YOLO import YOLO_util_get_model_path
from app.models.YOLO import YOLO
from app.logging.setup_logging import get_logger
from app.config.settings import (
    PICTO_CLUSTERING_CONF_THRESHOLD,
    PICTO_CLUSTERING_BLUR_THRESHOLD,
    PICTO_CLUSTERING_MIN_FACE_SIZE,
)
from app.utils.face_quality import face_passes_quality_gate

# Initialize logger
logger = get_logger(__name__)


class FaceDetectionResult(TypedDict):
    """Faces that passed the quality gate; the three lists are index-aligned."""

    embeddings: List[np.ndarray]  # L2-normalised FaceNet vectors
    bboxes: List[Dict[str, int]]  # x, y, width, height in source-image pixels
    confidences: List[float]
    faces_skipped: int  # detections rejected by the quality gate


class FaceDetector:
    def __init__(self):
        self.yolo_detector = YOLO(
            YOLO_util_get_model_path("face"),
            conf_threshold=PICTO_CLUSTERING_CONF_THRESHOLD,
            iou_threshold=0.45,
        )
        self.facenet = FaceNet(FaceNet_util_get_model_path())
        self._initialized = True
        logger.info("FaceDetector initialized with YOLO and FaceNet models.")

    def detect_faces(self, image_path: str) -> Optional[FaceDetectionResult]:
        """Detect and embed the faces in an image file. Pure inference: the caller
        persists them, so photos, face search and video keyframes share this path.
        """
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return None

        boxes, scores, _ = self.yolo_detector(img)
        logger.debug(f"Face detection boxes: {boxes}")
        logger.info(f"Detected {len(boxes)} faces in {image_path}.")

        embeddings, bboxes, confidences = [], [], []
        faces_skipped = 0

        for box, score in zip(boxes, scores):
            x1, y1, x2, y2 = map(int, box)

            padding = 20
            face_img = img[
                max(0, y1 - padding) : min(img.shape[0], y2 + padding),
                max(0, x1 - padding) : min(img.shape[1], x2 + padding),
            ]

            if not face_passes_quality_gate(
                face_crop=face_img,
                bbox=(x1, y1, x2, y2),
                conf_score=float(score),
                conf_threshold=self.yolo_detector.conf_threshold,
                blur_threshold=PICTO_CLUSTERING_BLUR_THRESHOLD,
                min_face_size=PICTO_CLUSTERING_MIN_FACE_SIZE,
            ):
                faces_skipped += 1
                continue

            # Create bounding box dictionary in JSON format
            bbox = {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}
            bboxes.append(bbox)
            confidences.append(float(score))

            processed_face = FaceNet_util_preprocess_image(face_img)
            embedding = self.facenet.get_embedding(processed_face)
            embeddings.append(embedding)

        return FaceDetectionResult(
            embeddings=embeddings,
            bboxes=bboxes,
            confidences=confidences,
            faces_skipped=faces_skipped,
        )

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
