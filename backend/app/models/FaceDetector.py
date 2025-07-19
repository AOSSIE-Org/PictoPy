# app/detectors/FaceDetector.py

import cv2
from app.models.FaceNet import FaceNet
from app.utils.FaceNet import FaceNet_util_preprocess_image, FaceNet_util_get_model_path
from app.utils.YOLO import YOLO_util_get_model_path
from app.models.YOLO import YOLO
from app.database.faces import db_insert_face_embeddings_by_image_id


class FaceDetector:
    _instance = None
    yolo_detector = None
    facenet = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceDetector, cls).__new__(cls)

            cls.yolo_detector = YOLO(
                YOLO_util_get_model_path("face"),
                conf_thres=0.35,
                iou_thres=0.45,
            )
            cls.facenet = FaceNet(FaceNet_util_get_model_path())

        return cls._instance

    def detect_faces(self, image_id: int, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return None

        boxes, scores, class_ids = self.yolo_detector(img)
        print(f"Detected {len(boxes)} faces in image {image_id}.")

        processed_faces, embeddings = [], []

        for box, score in zip(boxes, scores):
            if score > 0.3:
                x1, y1, x2, y2 = map(int, box)
                padding = 20
                face_img = img[
                    max(0, y1 - padding) : min(img.shape[0], y2 + padding),
                    max(0, x1 - padding) : min(img.shape[1], x2 + padding),
                ]
                processed_face = FaceNet_util_preprocess_image(face_img)
                processed_faces.append(processed_face)

                embedding = self.facenet.get_embedding(processed_face)
                embeddings.append(embedding)

        if embeddings:
            db_insert_face_embeddings_by_image_id(image_id, embeddings)

        return {
            "ids": f"{class_ids}",
            "processed_faces": processed_faces,
            "num_faces": len(embeddings),
        }

    @classmethod
    def close(cls):
        """
        Close and cleanup the FaceDetector singleton.
        This will reset the singleton instance and cleanup both YOLO detector and FaceNet.
        """
        if cls.yolo_detector is not None:
            # If YOLO detector has a cleanup method, call it
            if hasattr(cls.yolo_detector, "close"):
                cls.yolo_detector.close()
            elif hasattr(cls.yolo_detector, "cleanup"):
                cls.yolo_detector.cleanup()

            cls.yolo_detector = None

        if cls.facenet is not None:
            # If FaceNet has a cleanup method, call it
            if hasattr(cls.facenet, "close"):
                cls.facenet.close()
            elif hasattr(cls.facenet, "cleanup"):
                cls.facenet.cleanup()

            cls.facenet = None

        cls._instance = None
        print("FaceDetector singleton closed and cleaned up")

    def __del__(self):
        """
        Destructor to ensure cleanup when object is garbage collected.
        """
        self.close()
