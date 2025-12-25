import numpy as np
import cv2
from app.config import settings

class_names = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]

# Create a list of colors for each class where each color is a tuple of 3 integer values
rng = np.random.default_rng(3)
colors = rng.uniform(0, 255, size=(len(class_names), 3))


def YOLO_util_nms(boxes, scores, iou_threshold):
    """
    Perform Non-Maximum Suppression (NMS) on bounding boxes.

    NMS removes overlapping bounding boxes, keeping only the ones with highest
    confidence scores. Boxes with IoU above the threshold with a higher-scoring
    box are suppressed.

    Args:
        boxes: Array of bounding boxes with shape (N, 4) in (x1, y1, x2, y2) format
        scores: Array of confidence scores with shape (N,)
        iou_threshold: IoU threshold for suppression (0.0 to 1.0)

    Returns:
        List of indices of boxes to keep after NMS
    """
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the last box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of the picked box with the rest
        ious = YOLO_util_compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]

        # print(keep_indices.shape, sorted_indices.shape)
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def YOLO_util_multiclass_nms(boxes, scores, class_ids, iou_threshold):
    """
    Perform Non-Maximum Suppression (NMS) separately for each class.

    This function applies NMS independently for each object class, ensuring
    that boxes from different classes don't suppress each other.

    Args:
        boxes: Array of bounding boxes with shape (N, 4) in (x1, y1, x2, y2) format
        scores: Array of confidence scores with shape (N,)
        class_ids: Array of class IDs with shape (N,)
        iou_threshold: IoU threshold for suppression (0.0 to 1.0)

    Returns:
        List of indices of boxes to keep after multiclass NMS
    """
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
    Compute Intersection over Union (IoU) between one box and multiple boxes.

    IoU is calculated as the area of intersection divided by the area of union
    between bounding boxes. It measures the overlap between detected and ground
    truth boxes.

    Args:
        box: Single bounding box with shape (4,) in (x1, y1, x2, y2) format
        boxes: Array of bounding boxes with shape (N, 4) in (x1, y1, x2, y2) format

    Returns:
        Array of IoU values with shape (N,) for each box comparison
    """
    # Compute xmin, ymin, xmax, ymax for both boxes
    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    # Compute intersection area
    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    # Compute union area
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area = box_area + boxes_area - intersection_area

    # Compute IoU
    iou = intersection_area / union_area

    return iou


def YOLO_util_xywh2xyxy(x):
    """
    Convert bounding boxes from center format (x, y, w, h) to corner format (x1, y1, x2, y2).

    Args:
        x: Array of bounding boxes in (center_x, center_y, width, height) format

    Returns:
        Array of bounding boxes in (x1, y1, x2, y2) corner format where:
        - x1, y1: top-left corner coordinates
        - x2, y2: bottom-right corner coordinates
    """
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
    """
    Draw detection results on an image with bounding boxes, labels, and masks.

    Args:
        image: Input image as numpy array (BGR format)
        boxes: Array of bounding boxes with shape (N, 4)
        scores: Array of confidence scores with shape (N,)
        class_ids: Array of class IDs with shape (N,)
        mask_alpha: Transparency of the overlay mask (0.0 to 1.0)
        confidence_threshold: Minimum confidence to draw a detection

    Returns:
        Image with drawn detections as numpy array
    """
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
    """
    Draw a bounding box rectangle on an image.

    Args:
        image: Input image as numpy array
        box: Bounding box coordinates as (x1, y1, x2, y2)
        color: BGR color tuple for the box outline
        thickness: Line thickness in pixels

    Returns:
        Image with the drawn bounding box
    """
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
    """
    Draw text label above a bounding box with a filled background.

    Args:
        image: Input image as numpy array
        text: Text string to display
        box: Bounding box coordinates as (x1, y1, x2, y2)
        color: BGR color tuple for the text background
        font_size: Font scale factor
        text_thickness: Thickness of the text stroke

    Returns:
        Image with the drawn text label
    """
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
    """
    Draw semi-transparent colored masks over detected object regions.

    Args:
        image: Input image as numpy array
        boxes: Array of bounding boxes with shape (N, 4)
        classes: Array of class IDs with shape (N,) for color selection
        mask_alpha: Transparency of the masks (0.0 = invisible, 1.0 = opaque)

    Returns:
        Image with blended color masks overlaid on detection regions
    """
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
