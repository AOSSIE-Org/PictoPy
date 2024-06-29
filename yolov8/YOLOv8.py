import os
import time
import cv2
import numpy as np
import onnxruntime
from typing import List, Tuple

from yolov8.utils import xywh2xyxy, draw_detections, multiclass_nms, class_names


class YOLOv8:
    def __init__(self, path: str, conf_thres: float = 0.7, iou_thres: float = 0.5) -> None:
        """
        Initialize the YOLOv8 object detector.

        Args:
            path (str): The path to the YOLOv8 model file.
            conf_thres (float): The confidence threshold for object detection.
            iou_thres (float): The IoU threshold for non-maxima suppression.
        """
        self.conf_threshold = conf_thres
        self.iou_threshold = iou_thres

        # Initialize model
        self.initialize_model(path)

    def __call__(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Perform object detection on the given image.

        Args:
            image (np.ndarray): The input image.

        Returns:
            tuple: A tuple containing the bounding boxes, scores, and class IDs of the detected objects.
        """
        return self.detect_objects(image)

    def initialize_model(self, path: str) -> None:
        """
        Initialize the ONNX model.

        Args:
            path (str): The path to the YOLOv8 model file.
        """
        self.session = onnxruntime.InferenceSession(path, providers=onnxruntime.get_available_providers())
        # Get model info
        self.get_input_details()
        self.get_output_details()

    def detect_objects(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect objects in the given image.

        Args:
            image (np.ndarray): The input image.

        Returns:
            tuple: A tuple containing the bounding boxes, scores, and class IDs of the detected objects.
        """
        input_tensor = self.prepare_input(image)

        # Perform inference on the image
        outputs = self.inference(input_tensor)

        self.boxes, self.scores, self.class_ids = self.process_output(outputs)

        return self.boxes, self.scores, self.class_ids

    def prepare_input(self, image: np.ndarray) -> np.ndarray:
        """
        Prepare the input image for the model.

        Args:
            image (np.ndarray): The input image.

        Returns:
            np.ndarray: The preprocessed image tensor.
        """
        self.img_height, self.img_width = image.shape[:2]

        input_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize input image
        input_img = cv2.resize(input_img, (self.input_width, self.input_height))

        # Scale input pixel values to 0 to 1
        input_img = input_img / 255.0
        input_img = input_img.transpose(2, 0, 1)
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)

        return input_tensor

    def inference(self, input_tensor: np.ndarray) -> List[np.ndarray]:
        """
        Perform inference on the input tensor.

        Args:
            input_tensor (np.ndarray): The preprocessed image tensor.

        Returns:
            list: The model outputs.
        """
        start = time.perf_counter()
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})

        # print(f"Inference time: {(time.perf_counter() - start)*1000:.2f} ms")
        return outputs

    def process_output(self, output: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Process the model outputs to extract bounding boxes, scores, and class IDs.

        Args:
            output (list): The model outputs.

        Returns:
            tuple: A tuple containing the bounding boxes, scores, and class IDs of the detected objects.
        """
        predictions = np.squeeze(output[0]).T

        # Filter out object confidence scores below threshold
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > self.conf_threshold, :]
        scores = scores[scores > self.conf_threshold]

        if len(scores) == 0:
            return np.array([]), np.array([]), np.array([])

        # Get the class with the highest confidence
        class_ids = np.argmax(predictions[:, 4:], axis=1)

        # Get bounding boxes for each object
        boxes = self.extract_boxes(predictions)

        # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
        indices = multiclass_nms(boxes, scores, class_ids, self.iou_threshold)

        return boxes[indices], scores[indices], class_ids[indices]

    def extract_boxes(self, predictions: np.ndarray) -> np.ndarray:
        """
        Extract bounding boxes from the predictions.

        Args:
            predictions (np.ndarray): The model predictions.

        Returns:
            np.ndarray: The bounding boxes.
        """
        boxes = predictions[:, :4]
        boxes = self.rescale_boxes(boxes)
        boxes = xywh2xyxy(boxes)
        return boxes

    def rescale_boxes(self, boxes: np.ndarray) -> np.ndarray:
        """
        Rescale bounding boxes to the original image dimensions.

        Args:
            boxes (np.ndarray): The bounding boxes.

        Returns:
            np.ndarray: The rescaled bounding boxes.
        """
        input_shape = np.array([self.input_width, self.input_height, self.input_width, self.input_height])
        boxes = np.divide(boxes, input_shape, dtype=np.float32)
        boxes *= np.array([self.img_width, self.img_height, self.img_width, self.img_height])
        return boxes

    def draw_detections(self, image: np.ndarray, draw_scores: bool = True, mask_alpha: float = 0.4) -> np.ndarray:
        """
        Draw detections on the image.

        Args:
            image (np.ndarray): The input image.
            draw_scores (bool, optional): Whether to draw scores on the image. Defaults to True.
            mask_alpha (float, optional): The transparency of the mask. Defaults to 0.4.

        Returns:
            np.ndarray: The image with detections drawn on it.
        """
        return draw_detections(image, self.boxes, self.scores, self.class_ids, mask_alpha)

    def get_input_details(self) -> None:
        """
        Get the input details of the model.
        """
        model_inputs = self.session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]

        self.input_shape = model_inputs[0].shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]

    def get_output_details(self) -> None:
        """
        Get the output details of the model.
        """
        model_outputs = self.session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]


def save_image(image: cv2.Mat, filename: str):
    """
    Save an image to a file.

    Args:
        image (ndarray): The image to save.
        filename (str): The path to the output file.
    """
    cv2.imwrite(filename, image)


def prepend_to_file(folder_name: str, file_path: str) -> str:
    """
    Prepend a folder name to the path of a file before the filename.

    Args:
        folder_name (str): The name of the folder to prepend.
        file_path (str): The original path to the file.

    Returns:
        str: The modified path with the folder name prepended.
    """
    # Extract the base name (filename) from the file path
    base_name = os.path.basename(file_path)
    
    # Remove the base name from the file path to get the directory path
    dir_path = os.path.dirname(file_path)
    
    # Join the directory path with the folder name and the base name
    new_path = os.path.join(dir_path, folder_name, base_name)
    
    return new_path

def imgDetector(imgPath: str, model_path: str, conf_thres: float = 0.3, iou_thres: float = 0.5) -> Tuple[np.ndarray, YOLOv8]:
    """
    Load an image and object detector from YOLOv8 model.

    Args:
        imgPath (str): The path to the image file.
        model_path (str): The path to the YOLOv8 model file.
        conf_thres (float, optional): The confidence threshold for object detection. Defaults to 0.3.
        iou_thres (float, optional): The IoU threshold for non-maxima suppression. Defaults to 0.5.
    
    Returns:
        tuple: A tuple containing the image and the object detector.
    """
    return cv2.imread(imgPath), YOLOv8(model_path, conf_thres, iou_thres)

def markObjects(img: np.ndarray, yolov8_detector: YOLOv8) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect objects in an image using the YOLOv8 model.

    Args:
        img (ndarray): The image to detect objects in.
        yolov8_detector (YOLOv8): The YOLOv8 object detector.

    Returns:
        tuple: A tuple containing the following:
            - boxes (ndarray): The bounding boxes of the detected objects.
            - scores (ndarray): The confidence scores of the detected objects.
            - class_ids (ndarray): The class IDs of the detected objects.
    """
    return yolov8_detector.detect_objects(img)


def saveOutputImage(imgPath: str, img: np.ndarray, yolov8_detector: YOLOv8) -> None:
    """
    Save the image with detected objects to the output folder.

    Args:
        imgPath (str): The path to the original image file.
        img (ndarray): The image with detected objects.
        yolov8_detector (YOLOv8): The YOLOv8 object detector.
    """
    outputPath = prepend_to_file("output", imgPath)
    save_image(yolov8_detector.draw_detections(img), outputPath)


def uniqueClasses(class_ids: List[int]) -> List[str]:
    """
    Get a list of unique classes detected in the image.

    Args:
        class_ids (ndarray): The class IDs of the detected objects.

    Returns:
        list: A list of unique class names.
    """
    classes = []
    for id in np.unique(class_ids):
        classes.append(class_names[id])
    return classes


def detectedClass(imgPath: str) -> List[str]:
    """
    Detect objects in an image and return a list of unique classes.

    Args:
        imgPath (str): The path to the image file.

    Returns:
        list: A list of unique class names detected in the image.
    """
    model_path = "models/yolov8n.onnx"
    img, yolov8_detector = imgDetector(imgPath, model_path)
    _, _, class_ids = markObjects(img, yolov8_detector)
    saveOutputImage(imgPath, img, yolov8_detector)
    return uniqueClasses(class_ids)