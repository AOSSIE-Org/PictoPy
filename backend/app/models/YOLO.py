import onnxruntime
import time
import cv2
import numpy as np
from app.utils.YOLO import (
    YOLO_util_xywh2xyxy,
    YOLO_util_draw_detections,
    YOLO_util_multiclass_nms,
)
from app.utils.memory_monitor import log_memory_usage
from app.utils.ONNX import ONNX_util_get_execution_providers


class YOLO:
    def __init__(self, path, conf_threshold=0.7, iou_threshold=0.5):
        self.model_path = path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        # Create ONNX session once and reuse it
        self.session = onnxruntime.InferenceSession(self.model_path, providers=ONNX_util_get_execution_providers())

        # Initialize model info
        self.get_input_details()
        self.get_output_details()

    def __call__(self, image):
        return self.detect_objects(image)

    def close(self):
        del self.session  # Clean up the ONNX session
        print("YOLO model session closed.")

    @log_memory_usage
    def detect_objects(self, image):
        input_tensor = self.prepare_input(image)
        outputs = self.inference(input_tensor)
        self.boxes, self.scores, self.class_ids = self.process_output(outputs)
        return self.boxes, self.scores, self.class_ids

    def inference(self, input_tensor):
        time.perf_counter()
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})
        return outputs

    def get_input_details(self):
        model_inputs = self.session.get_inputs()
        self.input_names = [inp.name for inp in model_inputs]
        self.input_shape = model_inputs[0].shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]

    def get_output_details(self):
        model_outputs = self.session.get_outputs()
        self.output_names = [out.name for out in model_outputs]

    def prepare_input(self, image):
        self.img_height, self.img_width = image.shape[:2]
        input_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_img = cv2.resize(input_img, (self.input_width, self.input_height))
        input_img = input_img / 255.0
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
        return boxes

    def rescale_boxes(self, boxes):
        input_shape = np.array([self.input_width, self.input_height, self.input_width, self.input_height])
        boxes = np.divide(boxes, input_shape, dtype=np.float32)
        boxes *= np.array([self.img_width, self.img_height, self.img_width, self.img_height])
        return boxes

    def draw_detections(self, image, draw_scores=True, mask_alpha=0.4):
        return YOLO_util_draw_detections(image, self.boxes, self.scores, self.class_ids, mask_alpha)
