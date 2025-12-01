import cv2
from fastapi import HTTPException  # <-- add this
from app.models.YOLO import YOLO
from app.utils.YOLO import YOLO_util_get_model_path
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class ObjectClassifier:
    def __init__(self):
        self.yolo_classifier = YOLO(
            YOLO_util_get_model_path("object"), conf_threshold=0.4, iou_threshold=0.5
        )

    def get_classes(self, img_path) -> list[int] | None:
        img = cv2.imread(img_path)

        # FIX: Raise proper HTTPException instead of returning None
        if img is None:
            logger.error(f"Failed to load image: {img_path}")
            raise HTTPException(
                status_code=400,
                detail="Invalid or unreadable image file"
            )

        _, _, class_ids = self.yolo_classifier(img)
        logger.debug(f"Class IDs detected: {class_ids}")

        # convert class_ids to a list of integers
        return [int(class_id) for class_id in class_ids]

    def close(self):
        """Close and cleanup the ObjectClassifier."""
        if self.yolo_classifier is not None:
            self.yolo_classifier.close()
            self.yolo_classifier = None
