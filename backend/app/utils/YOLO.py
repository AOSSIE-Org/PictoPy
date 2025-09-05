"""
YOLO Object Detection Utilities

This module provides utility functions for YOLO-based object detection in PictoPy.
It includes functions for non-maximum suppression, IoU computation, bounding box
conversion, and visualization of detection results.

Key Features:
- COCO dataset class names and color mapping
- Non-maximum suppression for removing duplicate detections
- IoU (Intersection over Union) computation for bounding box overlap
- Bounding box format conversion utilities
- Detection visualization with bounding boxes and labels
- Model path resolution based on user preferences

The module supports both object detection and face detection models with
configurable model sizes (nano, small, medium) based on user preferences.
"""

# Standard library imports
import numpy as np
import cv2

# Application imports
from app.config import settings

# =============================================================================
# COCO DATASET CLASS NAMES
# =============================================================================

# COCO dataset class names for object detection
# These correspond to the 80 classes that YOLO models are trained to detect
class_names = [
    "person",        # 0
    "bicycle",       # 1
    "car",           # 2
    "motorcycle",    # 3
    "airplane",      # 4
    "bus",           # 5
    "train",         # 6
    "truck",         # 7
    "boat",          # 8
    "traffic light", # 9
    "fire hydrant",  # 10
    "stop sign",     # 11
    "parking meter", # 12
    "bench",         # 13
    "bird",          # 14
    "cat",           # 15
    "dog",           # 16
    "horse",         # 17
    "sheep",         # 18
    "cow",           # 19
    "elephant",      # 20
    "bear",          # 21
    "zebra",         # 22
    "giraffe",       # 23
    "backpack",      # 24
    "umbrella",      # 25
    "handbag",       # 26
    "tie",           # 27
    "suitcase",      # 28
    "frisbee",       # 29
    "skis",          # 30
    "snowboard",     # 31
    "sports ball",   # 32
    "kite",          # 33
    "baseball bat",  # 34
    "baseball glove", # 35
    "skateboard",    # 36
    "surfboard",     # 37
    "tennis racket", # 38
    "bottle",        # 39
    "wine glass",    # 40
    "cup",           # 41
    "fork",          # 42
    "knife",         # 43
    "spoon",         # 44
    "bowl",          # 45
    "banana",        # 46
    "apple",         # 47
    "sandwich",      # 48
    "orange",        # 49
    "broccoli",      # 50
    "carrot",        # 51
    "hot dog",       # 52
    "pizza",         # 53
    "donut",         # 54
    "cake",          # 55
    "chair",         # 56
    "couch",         # 57
    "potted plant",  # 58
    "bed",           # 59
    "dining table",  # 60
    "toilet",        # 61
    "tv",            # 62
    "laptop",        # 63
    "mouse",         # 64
    "remote",        # 65
    "keyboard",      # 66
    "cell phone",    # 67
    "microwave",     # 68
    "oven",          # 69
    "toaster",       # 70
    "sink",          # 71
    "refrigerator",  # 72
    "book",          # 73
    "clock",         # 74
    "vase",          # 75
    "scissors",      # 76
    "teddy bear",    # 77
    "hair drier",    # 78
    "toothbrush",    # 79
]

# =============================================================================
# VISUALIZATION COLORS
# =============================================================================

# Generate consistent random colors for each class using a fixed seed
# This ensures the same colors are used across different runs
rng = np.random.default_rng(3)  # Fixed seed for reproducible colors
colors = rng.uniform(0, 255, size=(len(class_names), 3))


# =============================================================================
# NON-MAXIMUM SUPPRESSION (NMS) FUNCTIONS
# =============================================================================

def YOLO_util_nms(boxes, scores, iou_threshold):
    """
    Apply Non-Maximum Suppression to remove overlapping bounding boxes.
    
    This function implements the standard NMS algorithm to eliminate duplicate
    detections by keeping only the highest-scoring box when multiple boxes
    have significant overlap (IoU > threshold).
    
    Args:
        boxes: Array of bounding boxes in format [x1, y1, x2, y2]
        scores: Array of confidence scores for each box
        iou_threshold: IoU threshold for considering boxes as overlapping
        
    Returns:
        List of indices of boxes to keep after NMS
    """
    # Sort boxes by confidence score in descending order
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the box with highest confidence score
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of the selected box with all remaining boxes
        ious = YOLO_util_compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Keep only boxes with IoU below the threshold (non-overlapping)
        keep_indices = np.where(ious < iou_threshold)[0]

        # Update the list of remaining boxes
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def YOLO_util_multiclass_nms(boxes, scores, class_ids, iou_threshold):
    unique_class_ids = np.unique(class_ids)

    keep_boxes = []
    for class_id in unique_class_ids:
        class_indices = np.where(class_ids == class_id)[0]
        class_boxes = boxes[class_indices, :]
        class_scores = scores[class_indices]

        class_keep_boxes = YOLO_util_nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def YOLO_util_compute_iou(box, boxes):
    """
    Compute Intersection over Union (IoU) between a single box and multiple boxes.
    
    IoU is a measure of overlap between two bounding boxes, calculated as:
    IoU = intersection_area / union_area
    
    Args:
        box: Single bounding box [x1, y1, x2, y2]
        boxes: Array of bounding boxes [N, 4] in format [x1, y1, x2, y2]
        
    Returns:
        Array of IoU values between the single box and each box in the array
    """
    # Compute intersection coordinates
    xmin = np.maximum(box[0], boxes[:, 0])  # Left edge of intersection
    ymin = np.maximum(box[1], boxes[:, 1])  # Top edge of intersection
    xmax = np.minimum(box[2], boxes[:, 2])  # Right edge of intersection
    ymax = np.minimum(box[3], boxes[:, 3])  # Bottom edge of intersection

    # Compute intersection area (0 if no intersection)
    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    # Compute individual box areas
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    
    # Compute union area (sum of areas minus intersection)
    union_area = box_area + boxes_area - intersection_area

    # Compute IoU (handle division by zero)
    iou = intersection_area / union_area

    return iou


def YOLO_util_xywh2xyxy(x):
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def YOLO_util_draw_detections(
    image, boxes, scores, class_ids, mask_alpha=0.3, confidence_threshold=0.3
):
    det_img = image.copy()

    img_height, img_width = image.shape[:2]
    font_size = min([img_height, img_width]) * 0.0006
    text_thickness = int(min([img_height, img_width]) * 0.001)

    det_img = YOLO_util_draw_masks(det_img, boxes, class_ids, mask_alpha)

    # Draw bounding boxes and labels of detections
    for class_id, box, score in zip(class_ids, boxes, scores):
        if score < confidence_threshold or class_id >= len(class_names) - 1:
            color = colors[-1]
            label = "unknown"
        else:
            color = colors[class_id]
            label = class_names[class_id]
        YOLO_util_draw_box(det_img, box, color)
        caption = f"{label} {int(score * 100)}%"
        YOLO_util_draw_text(det_img, caption, box, color, font_size, text_thickness)

    return det_img


def YOLO_util_draw_box(
    image: np.ndarray,
    box: np.ndarray,
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
) -> np.ndarray:
    x1, y1, x2, y2 = box.astype(int)
    return cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)


def YOLO_util_draw_text(
    image: np.ndarray,
    text: str,
    box: np.ndarray,
    color: tuple[int, int, int] = (0, 0, 255),
    font_size: float = 0.001,
    text_thickness: int = 2,
) -> np.ndarray:
    x1, y1, x2, y2 = box.astype(int)
    (tw, th), _ = cv2.getTextSize(
        text=text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_size,
        thickness=text_thickness,
    )
    th = int(th * 1.2)

    cv2.rectangle(image, (x1, y1), (x1 + tw, y1 - th), color, -1)

    return cv2.putText(
        image,
        text,
        (x1, y1),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_size,
        (255, 255, 255),
        text_thickness,
        cv2.LINE_AA,
    )


def YOLO_util_draw_masks(
    image: np.ndarray, boxes: np.ndarray, classes: np.ndarray, mask_alpha: float = 0.3
) -> np.ndarray:
    mask_img = image.copy()

    # Draw bounding boxes and labels of detections
    for box, class_id in zip(boxes, classes):
        color = colors[class_id]

        x1, y1, x2, y2 = box.astype(int)

        # Draw fill rectangle in mask image
        cv2.rectangle(mask_img, (x1, y1), (x2, y2), color, -1)

    return cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0)


def YOLO_util_get_model_path(model_type: str = "object") -> str:
    """
    Get the YOLO model path based on user preferences from metadata.

    Args:
        model_type: Type of model ("object" or "face")

    Returns:
        str: Path to the appropriate YOLO model file
    """
    from app.database.metadata import db_get_metadata

    # Get metadata from database
    metadata = db_get_metadata()

    # Default model size if no preferences found
    model_size = "small"

    # Extract YOLO model size from user preferences
    if metadata and "user_preferences" in metadata:
        user_prefs = metadata["user_preferences"]
        model_size = user_prefs.get("YOLO_model_size", "small")

    # Define model mappings
    model_mappings = {
        "object": {
            "nano": settings.NANO_OBJ_DETECTION_MODEL,
            "small": settings.SMALL_OBJ_DETECTION_MODEL,
            "medium": settings.MEDIUM_OBJ_DETECTION_MODEL,
        },
        "face": {
            "nano": settings.NANO_FACE_DETECTION_MODEL,
            "small": settings.SMALL_FACE_DETECTION_MODEL,
            "medium": settings.MEDIUM_FACE_DETECTION_MODEL,
        },
    }

    # Get the appropriate model mapping
    models = model_mappings.get(model_type, model_mappings["object"])

    # Return the model path with fallback to small
    return models.get(model_size, models["small"])
