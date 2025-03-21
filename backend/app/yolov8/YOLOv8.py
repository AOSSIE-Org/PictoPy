import time
import cv2
import numpy as np
from app.utils.onnx_manager import onnx_session
from app.yolov8.utils import xywh2xyxy, draw_detections, multiclass_nms
from app.utils.memory_monitor import log_memory_usage


class YOLOv8:
    def __init__(self, path, conf_thres=0.7, iou_thres=0.5):
        self.model_path = path
        self.conf_threshold = conf_thres
        self.iou_threshold = iou_thres

    def __call__(self, image):
        with onnx_session(self.model_path) as session:
            self.get_input_details(session)
            self.get_output_details(session)
            return self.detect_objects(image)

    @log_memory_usage
    def detect_objects(self, image):
        with onnx_session(self.model_path) as session:
            input_tensor = self.prepare_input(image)
            outputs = self.inference(session, input_tensor)
            self.boxes, self.scores, self.class_ids = self.process_output(outputs)
            return self.boxes, self.scores, self.class_ids

    def inference(self, session, input_tensor):
        time.perf_counter()
        outputs = session.run(self.output_names, {self.input_names[0]: input_tensor})
        return outputs

    def get_input_details(self, session):
        model_inputs = session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]
        self.input_shape = model_inputs[0].shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]

    def get_output_details(self, session):
        model_outputs = session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]

    def prepare_input(self, image):
        self.img_height, self.img_width = image.shape[:2]

        input_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize input image
        input_img = cv2.resize(input_img, (self.input_width, self.input_height))

        # Scale input pixel values to 0 to 1
        input_img = input_img / 255.0
        input_img = input_img.transpose(2, 0, 1)
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)

        return input_tensor

    def process_output(self, output):
        predictions = np.squeeze(output[0]).T

        # Filter out object confidence scores below threshold
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > self.conf_threshold, :]
        scores = scores[scores > self.conf_threshold]

        if len(scores) == 0:
            return [], [], []

        # Get the class with the highest confidence
        class_ids = np.argmax(predictions[:, 4:], axis=1)

        # Get bounding boxes for each object
        boxes = self.extract_boxes(predictions)

        # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
        # indices = nms(boxes, scores, self.iou_threshold)
        indices = multiclass_nms(boxes, scores, class_ids, self.iou_threshold)

        return boxes[indices], scores[indices], class_ids[indices]

    def extract_boxes(self, predictions):
        # Extract boxes from predictions
        boxes = predictions[:, :4]

        # Scale boxes to original image dimensions
        boxes = self.rescale_boxes(boxes)

        # Convert boxes to xyxy format
        boxes = xywh2xyxy(boxes)

        return boxes

    def rescale_boxes(self, boxes):

        # Rescale boxes to original image dimensions
        input_shape = np.array(
            [self.input_width, self.input_height, self.input_width, self.input_height]
        )
        boxes = np.divide(boxes, input_shape, dtype=np.float32)
        boxes *= np.array(
            [self.img_width, self.img_height, self.img_width, self.img_height]
        )
        return boxes

    def draw_detections(self, image, draw_scores=True, mask_alpha=0.4):

        return draw_detections(
            image, self.boxes, self.scores, self.class_ids, mask_alpha
        )


if __name__ == "__main__":
    from imread_from_url import imread_from_url

    model_path = "../models/yolov8m.onnx"

    # Initialize YOLOv8 object detector
    yolov8_detector = YOLOv8(model_path, conf_thres=0.3, iou_thres=0.5)

    img_url = "https://live.staticflickr.com/13/19041780_d6fd803de0_3k.jpg"
    img = imread_from_url(img_url)

    # Detect Objects
    yolov8_detector(img)

    # Draw detections
    combined_img = yolov8_detector.draw_detections(img)
    cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
    cv2.imshow("Output", combined_img)
    cv2.waitKey(0)
