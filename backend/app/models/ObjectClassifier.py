import cv2
from app.models.YOLO import YOLO
from app.utils.YOLO import YOLO_util_get_model_path


class ObjectClassifier:
    def __init__(self):
        self.yolo_classifier = YOLO(
            YOLO_util_get_model_path("object"), conf_threshold=0.4, iou_threshold=0.5
        )

    def get_classes(self, img_path) -> list[int] | None:
        img = cv2.imread(img_path)
        if img is None:
            print(f"Failed to load image: {img_path}")
            return None

        _, _, class_ids = self.yolo_classifier(img)
        print(class_ids, flush=True)
        # convert class_ids to a list of integers from numpy array
        class_ids = [int(class_id) for class_id in class_ids]
        return class_ids

    def close(self):
        """
        Close and cleanup the ObjectClassifier.
        """
        if self.yolo_classifier is not None:
            self.yolo_classifier.close()
            self.yolo_classifier = None
