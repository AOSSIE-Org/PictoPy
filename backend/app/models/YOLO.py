import cv2
from fastapi import HTTPException
from app.utils.YOLO import YOLO_util_get_model_path
from app.logging.setup_logging import get_logger
import numpy as np
import onnxruntime as ort

logger = get_logger(__name__)


class YOLO:
    def __init__(self, model_path: str, conf_threshold=0.4, iou_threshold=0.5):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        try:
            self.session = ort.InferenceSession(model_path)
            logger.info(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize YOLO model"
            )

    def __call__(self, img_path_or_array):
        """
        Accepts either an image path (str) or a numpy array
        and returns YOLO detections.
        """

        # If string, treat as path
        if isinstance(img_path_or_array, str):
            img = cv2.imread(img_path_or_array)

            # SECURITY + CONSISTENCY FIX
            if img is None:
                logger.error(f"Failed to load image: {img_path_or_array}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or unreadable image file"
                )
        else:
            # If numpy array, assume valid
            img = img_path_or_array

        # ----- PREPROCESS -----
        input_blob = cv2.resize(img, (640, 640))
        input_blob = input_blob.transpose(2, 0, 1)[None].astype(np.float32)

        # ----- INFERENCE -----
        try:
            output = self.session.run(None, {"images": input_blob})[0]
        except Exception as e:
            logger.error(f"YOLO inference failure: {e}")
            raise HTTPException(
                status_code=500,
                detail="Model inference error"
            )

        # ----- POSTPROCESS -----
        boxes, scores, class_ids = self._postprocess(output)
        return boxes, scores, class_ids

    def _postprocess(self, output):
        """
        Convert YOLO output to bounding boxes, scores, class IDs.
        (Simplified placeholder — real code inside your repo)
        """
        # TODO: model-specific decoding logic
        return [], [], []

    def close(self):
        """Release model resources."""
        self.session = None
