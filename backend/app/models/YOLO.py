from __future__ import annotations

import onnxruntime
import time
import cv2
import numpy as np
from app.models.model_registry import MODEL_REGISTRY, get_model_key_from_path
from app.models.session_registry import (
    mark_model_session_active,
    mark_model_session_inactive,
)
from app.utils.YOLO import (
    YOLO_util_xywh2xyxy,
    YOLO_util_draw_detections,
    YOLO_util_multiclass_nms,
)
from app.utils.memory_monitor import log_memory_usage
from app.utils.ONNX import ONNX_util_get_execution_providers
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class YOLO:
    def __init__(self, path, conf_threshold=0.7, iou_threshold=0.5):
        self.model_path = path
        self._model_key = get_model_key_from_path(path)
        self._session_registered = False
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self._session = None
        import threading

        self._lock = threading.Lock()

    def get_session(self):
        session = self._session
        if session is not None:
            return session

        with self._lock:
            if self._session is None:
                import os

                if not os.path.exists(self.model_path):
                    model_key = None
                    for key, spec in MODEL_REGISTRY.items():
                        if spec["filename"] in self.model_path:
                            model_key = key
                            break
                    model_name = (
                        model_key if model_key else os.path.basename(self.model_path)
                    )
                    raise RuntimeError(
                        f"Model '{model_name}' is not installed. "
                        "Please install it from Settings → AI Models before using this feature."
                    )

                self._session = onnxruntime.InferenceSession(
                    self.model_path, providers=ONNX_util_get_execution_providers()
                )
                if self._model_key is not None and not self._session_registered:
                    try:
                        mark_model_session_active(self._model_key)
                    except RuntimeError:
                        self._session = None
                        raise
                    self._session_registered = True
                # Initialize model info once session is created
                self.get_input_details()
                self.get_output_details()

            return self._session

    def __call__(self, image):
        return self.detect_objects(image)

    def close(self):
        with self._lock:
            if self._session is not None:
                self._session = None
                if self._model_key is not None and self._session_registered:
                    mark_model_session_inactive(self._model_key)
                    self._session_registered = False
        logger.info("YOLO model session closed.")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    @log_memory_usage
    def detect_objects(self, image):
        session = self.get_session()
        input_tensor = self.prepare_input(image)
        outputs = self.inference(input_tensor, session=session)
        self.boxes, self.scores, self.class_ids = self.process_output(outputs)
        return self.boxes, self.scores, self.class_ids

    def inference(self, input_tensor, session=None):
        start = time.perf_counter()
        if session is None:
            session = self.get_session()
        outputs = session.run(self.output_names, {self.input_names[0]: input_tensor})
        logger.debug("Inference completed in %.4fs", time.perf_counter() - start)
        return outputs

    def get_input_details(self):
        model_inputs = self._session.get_inputs()
        self.input_names = [inp.name for inp in model_inputs]
        self.input_shape = model_inputs[0].shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]

    def get_output_details(self):
        model_outputs = self._session.get_outputs()
        self.output_names = [out.name for out in model_outputs]

    def prepare_input(self, image):
        self.img_height, self.img_width = image.shape[:2]
        input_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Letterbox: resize preserving aspect ratio, pad the rest with gray
        self.scale = min(
            self.input_width / self.img_width, self.input_height / self.img_height
        )
        new_w = round(self.img_width * self.scale)
        new_h = round(self.img_height * self.scale)
        self.pad_x = (self.input_width - new_w) // 2
        self.pad_y = (self.input_height - new_h) // 2
        resized = cv2.resize(input_img, (new_w, new_h))
        padded = np.full(
            (self.input_height, self.input_width, 3), 114, dtype=input_img.dtype
        )
        padded[self.pad_y : self.pad_y + new_h, self.pad_x : self.pad_x + new_w] = (
            resized
        )
        input_img = padded / 255.0
        input_img = input_img.transpose(2, 0, 1)
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)
        return input_tensor

    def process_output(self, output):
        predictions = np.squeeze(output[0]).T
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > self.conf_threshold]
        scores = scores[scores > self.conf_threshold]

        if len(scores) == 0:
            return [], [], []

        class_ids = np.argmax(predictions[:, 4:], axis=1)
        boxes = self.extract_boxes(predictions)
        indices = YOLO_util_multiclass_nms(boxes, scores, class_ids, self.iou_threshold)

        return boxes[indices], scores[indices], class_ids[indices]

    def extract_boxes(self, predictions):
        boxes = predictions[:, :4]
        boxes = self.rescale_boxes(boxes)
        boxes = YOLO_util_xywh2xyxy(boxes)
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, self.img_width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, self.img_height)
        return boxes

    def rescale_boxes(self, boxes):
        # Undo the letterbox: remove padding offset, then unscale (boxes are xywh)
        boxes = boxes.astype(np.float32).copy()
        boxes[:, 0] = (boxes[:, 0] - self.pad_x) / self.scale
        boxes[:, 1] = (boxes[:, 1] - self.pad_y) / self.scale
        boxes[:, 2:4] /= self.scale
        return boxes

    def draw_detections(self, image, draw_scores=True, mask_alpha=0.4):
        return YOLO_util_draw_detections(
            image, self.boxes, self.scores, self.class_ids, mask_alpha
        )
