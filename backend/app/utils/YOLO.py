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
    Performs Non-Maximum Suppression (NMS) to filter overlapping boxes.

    Keeps boxes with highest scores and removes boxes with IoU above
    the threshold.

    Args:
        boxes (np.ndarray): Bounding boxes [x1, y1, x2, y2], shape (N, 4).
        scores (np.ndarray): Confidence scores for each box.
        iou_threshold (float): IoU threshold for suppression.

    Returns:
        list: Indices of boxes kept after NMS.
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
    Applies class-wise Non-Maximum Suppression (NMS) to filter overlapping boxes.

    Args:
        boxes (np.ndarray): Bounding boxes, shape (N, 4) [x1, y1, x2, y2].
        scores (np.ndarray): Confidence scores for each box.
        class_ids (np.ndarray): Class IDs for each box.
        iou_threshold (float): IoU threshold to suppress boxes within the same class.

    Returns:
        list: Indices of boxes kept after class-wise NMS.
    """

    # Get all unique class IDs present in the predictions
    # Example: [0, 0, 1, 2, 2] -> [0, 1, 2]
    unique_class_ids = np.unique(class_ids)

    # List to store the final indices of selected bounding boxes
    keep_boxes = []

    # Apply Non-Maximum Suppression separately for each class
    for class_id in unique_class_ids:

        # Get indices of bounding boxes belonging to the current class
        class_indices = np.where(class_ids == class_id)[0]

        # Select bounding boxes corresponding to the current class
        class_boxes = boxes[class_indices, :]

        # Select confidence scores corresponding to the current class
        class_scores = scores[class_indices]

        # Apply standard Non-Maximum Suppression on the current class
        # to remove highly overlapping bounding boxes
        class_keep_boxes = YOLO_util_nms(class_boxes, class_scores, iou_threshold)

        # Map the kept class-level indices back to the original indices
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def YOLO_util_compute_iou(box, boxes):
    """
    Computes IoU between a single bounding box and multiple boxes.

    Args:
        box (np.ndarray): Single bounding box [x1, y1, x2, y2].
        boxes (np.ndarray): Array of bounding boxes of shape (N, 4).

    Returns:
        np.ndarray: IoU values between `box` and each box in `boxes`.
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
    Converts bounding boxes from (x, y, w, h) format to (x1, y1, x2, y2) format.

    Args:
        x (np.ndarray): Bounding boxes in (x, y, w, h) format, where (x, y)
            represents the center and (w, h) represents width and height.

    Returns:
        np.ndarray: Bounding boxes in (x1, y1, x2, y2) corner format.
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
    Visualizes object detections by drawing masks, bounding boxes,
    and class labels on the input image.

    Args:
        image (np.ndarray): Input image on which detections are drawn.
        boxes (np.ndarray): Bounding boxes in (x1, y1, x2, y2) format.
        scores (np.ndarray): Confidence scores for each detection.
        class_ids (np.ndarray): Class IDs for each detection.
        mask_alpha (float, optional): Transparency of segmentation masks.
        confidence_threshold (float, optional): Minimum score to display labels.

    Returns:
        np.ndarray: Image with visualized detection results.
    """

    # Create a copy of the input image to avoid modifying the original
    det_img = image.copy()

    # Get image dimensions
    img_height, img_width = image.shape[:2]

    # Dynamically compute font size based on image size
    font_size = min([img_height, img_width]) * 0.0006

    # Dynamically compute text thickness based on image size
    text_thickness = int(min([img_height, img_width]) * 0.001)

    # Draw segmentation masks with given transparency (mask_alpha)
    det_img = YOLO_util_draw_masks(det_img, boxes, class_ids, mask_alpha)

    # Draw bounding boxes and labels of detections
    for class_id, box, score in zip(class_ids, boxes, scores):

        # If detection score is too low or class is invalid
        if score < confidence_threshold or class_id >= len(class_names) - 1:
            color = colors[-1]
            label = "unknown"
        else:
            color = colors[class_id]
            label = class_names[class_id]

        # Draw bounding box for this detection
        YOLO_util_draw_box(det_img, box, color)

        # Prepare label text (class name + confidence %)
        caption = f"{label} {int(score * 100)}%"

        # Draw label text above the bounding box
        YOLO_util_draw_text(det_img, caption, box, color, font_size, text_thickness)

    return det_img


def YOLO_util_draw_box(
    image: np.ndarray,
    box: np.ndarray,
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draws a bounding box on the given image.

    Args:
        image (np.ndarray): Input image on which the box will be drawn.
        box (np.ndarray): Bounding box coordinates [x1, y1, x2, y2].
        color (tuple[int, int, int], optional): Box color in BGR format.
            Defaults to red (0, 0, 255).
        thickness (int, optional): Thickness of the box border in pixels.
            Defaults to 2.

    Returns:
        np.ndarray: Image with the bounding box drawn.
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
    Draws a text label above a bounding box on the image.

    Args:
        image (np.ndarray): Input image on which the text will be drawn.
        text (str): Text label to display.
        box (np.ndarray): Bounding box coordinates [x1, y1, x2, y2].
        color (tuple[int, int, int], optional): Background color for the text box.
            Defaults to red (0, 0, 255).
        font_size (float, optional): Font scale for the text.
            Defaults to 0.001 (scaled by image size in parent function).
        text_thickness (int, optional): Thickness of the text.
            Defaults to 2.

    Returns:
        np.ndarray: Image with the text label drawn above the bounding box.
    """

    # Convert bounding box coordinates to integers for OpenCV
    x1, y1, x2, y2 = box.astype(int)

    # Compute text size (width and height) for the given font and thickness
    (tw, th), _ = cv2.getTextSize(
        text=text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_size,
        thickness=text_thickness,
    )

    # Add a little padding to the text height for better background rectangle
    th = int(th * 1.2)

    # Draw filled rectangle as background for text label
    # Top-left corner: (x1, y1)
    # Bottom-right corner: (x1 + tw, y1 - th)
    # 'color' defines rectangle color, -1 fills the rectangle
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
    Overlays semi-transparent colored masks on detected objects in the image.

    Args:
        image (np.ndarray): Input image on which masks will be drawn.
        boxes (np.ndarray): Bounding boxes of detected objects [x1, y1, x2, y2].
        classes (np.ndarray): Class IDs corresponding to each bounding box.
        mask_alpha (float, optional): Transparency factor for masks.
            Defaults to 0.3.

    Returns:
        np.ndarray: Image with semi-transparent colored masks overlayed.
    """

    # Make a copy of the input image to draw masks on
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
