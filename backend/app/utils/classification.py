import cv2
from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL
from app.yolov8.YOLOv8 import YOLOv8


class ObjectClassifier:
    _instance = None
    _detector = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObjectClassifier, cls).__new__(cls)
            cls._detector = YOLOv8(DEFAULT_OBJ_DETECTION_MODEL, conf_thres=0.4, iou_thres=0.5)
        return cls._instance

    def get_classes(self, img_path) -> list[int] | None:
        img = cv2.imread(img_path)
        if img is None:
            print(f"Failed to load image: {img_path}")
            return None

        _, _, class_ids = self._detector(img)
        print(class_ids, flush=True)
        # convert class_ids to a list of integers from numpy array
        class_ids = [int(class_id) for class_id in class_ids]
        return class_ids


# Usage example:
# classifier = ObjectClassifier()
# classes = classifier.get_classes("path/to/image.jpg")
