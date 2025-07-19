import cv2
from app.models.YOLO import YOLO
from app.utils.YOLO import YOLO_util_get_model_path


class ObjectClassifier:
    _instance = None
    yolo_classifier = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObjectClassifier, cls).__new__(cls)
            print(
                "Using YOLO model path:", YOLO_util_get_model_path("object")
            )  # Debugging line
            cls.yolo_classifier = YOLO(
                YOLO_util_get_model_path("object"), conf_thres=0.4, iou_thres=0.5
            )
        return cls._instance

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

    @classmethod
    def close(cls):
        """
        Close and cleanup the ObjectClassifier singleton.
        This will reset the singleton instance and cleanup the YOLO classifier.
        """
        if cls.yolo_classifier is not None:
            # If YOLO class has a cleanup method, call it
            if hasattr(cls.yolo_classifier, "close"):
                cls.yolo_classifier.close()
            elif hasattr(cls.yolo_classifier, "cleanup"):
                cls.yolo_classifier.cleanup()

            cls.yolo_classifier = None

        cls._instance = None
        print("ObjectClassifier singleton closed and cleaned up")

    def __del__(self):
        """
        Destructor to ensure cleanup when object is garbage collected.
        """
        self.close()
