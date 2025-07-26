import numpy as np
import cv2

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


def nms(boxes, scores, iou_threshold):
    # Performs Non-Maximum Suppression (NMS) on bounding boxes for a single class.
    # Keeps boxes with the highest scores and removes overlapping boxes based on IoU threshold.
    # Inputs:
    #   boxes - np.array of shape (N, 4) with bounding boxes (x1, y1, x2, y2)
    #   scores - np.array of shape (N,) with confidence scores
    #   iou_threshold - float IoU threshold to filter overlapping boxes
    # Returns:
    #   keep_boxes - list of indices of boxes to keep after suppression

    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the highest scoring box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of this box with the rest
        ious = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]

        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def multiclass_nms(boxes, scores, class_ids, iou_threshold):
    # Applies Non-Maximum Suppression (NMS) separately for each class in multi-class detections.
    # Inputs:
    #   boxes - np.array of shape (N, 4)
    #   scores - np.array of shape (N,)
    #   class_ids - np.array of shape (N,) with class indices
    #   iou_threshold - float threshold for NMS
    # Returns:
    #   keep_boxes - list of indices of boxes kept after NMS for all classes

    unique_class_ids = np.unique(class_ids)

    keep_boxes = []
    for class_id in unique_class_ids:
        # Select boxes, scores for current class
        class_indices = np.where(class_ids == class_id)[0]
        class_boxes = boxes[class_indices, :]
        class_scores = scores[class_indices]

        # Perform NMS for current class boxes
        class_keep_boxes = nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def compute_iou(box, boxes):
    # Computes Intersection over Union (IoU) between one box and multiple boxes.
    # Inputs:
    #   box - np.array shape (4,) single box (x1, y1, x2, y2)
    #   boxes - np.array shape (N, 4) multiple boxes
    # Returns:
    #   iou - np.array shape (N,) IoU values

    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area = box_area + boxes_area - intersection_area

    iou = intersection_area / union_area

    return iou


def xywh2xyxy(x):
    # Converts bounding boxes from (center_x, center_y, width, height) format to
    # (x1, y1, x2, y2) format.
    # Inputs:
    #   x - np.array with shape (..., 4) bounding boxes in xywh format
    # Returns:
    #   y - np.array with same shape as x, boxes in xyxy format

    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def draw_detections(
    image, boxes, scores, class_ids, mask_alpha=0.3, confidence_threshold=0.3
):
    # Draws detection results on the image including masks, bounding boxes, and labels.
    # Inputs:
    #   image - input image as np.array
    #   boxes - np.array of bounding boxes (x1, y1, x2, y2)
    #   scores - np.array of confidence scores
    #   class_ids - np.array of class indices
    #   mask_alpha - transparency for masks
    #   confidence_threshold - minimum score to draw a detection
    # Returns:
    #   det_img - image with detections drawn

    det_img = image.copy()

    img_height, img_width = image.shape[:2]
    font_size = min([img_height, img_width]) * 0.0006
    text_thickness = int(min([img_height, img_width]) * 0.001)

    det_img = draw_masks(det_img, boxes, class_ids, mask_alpha)

    # Draw bounding boxes and labels
    for class_id, box, score in zip(class_ids, boxes, scores):
        if score < confidence_threshold or class_id >= len(class_names) - 1:
            color = colors[-1]
            label = "unknown"
        else:
            color = colors[class_id]
            label = class_names[class_id]
        draw_box(det_img, box, color)
        caption = f"{label} {int(score * 100)}%"
        draw_text(det_img, caption, box, color, font_size, text_thickness)

    return det_img


def draw_box(
    image: np.ndarray,
    box: np.ndarray,
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
) -> np.ndarray:
    # Draws a rectangle (bounding box) on the image.
    # Inputs:
    #   image - input image as np.array
    #   box - bounding box coordinates (x1, y1, x2, y2)
    #   color - BGR color tuple
    #   thickness - line thickness
    # Returns:
    #   image with rectangle drawn

    x1, y1, x2, y2 = box.astype(int)
    return cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)


def draw_text(
    image: np.ndarray,
    text: str,
    box: np.ndarray,
    color: tuple[int, int, int] = (0, 0, 255),
    font_size: float = 0.001,
    text_thickness: int = 2,
) -> np.ndarray:
    # Draws text label above the bounding box on the image.
    # Inputs:
    #   image - input image as np.array
    #   text - string to draw
    #   box - bounding box coordinates (x1, y1, x2, y2)
    #   color - background color of text box
    #   font_size - scale of text
    #   text_thickness - thickness of text characters
    # Returns:
    #   image with text drawn

    x1, y1, x2, y2 = box.astype(int)
    (tw, th), _ = cv2.getTextSize(
        text=text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_size,
        thickness=text_thickness,
    )
    th = int(th * 1.2)

    # Draw filled rectangle as background for text
    cv2.rectangle(image, (x1, y1), (x1 + tw, y1 - th), color, -1)

    # Put white text over rectangle
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


def draw_masks(
    image: np.ndarray, boxes: np.ndarray, classes: np.ndarray, mask_alpha: float = 0.3
) -> np.ndarray:
    # Draws semi-transparent colored masks on the image based on bounding boxes.
    # Inputs:
    #   image - input image as np.array
    #   boxes - np.array of bounding boxes (x1, y1, x2, y2)
    #   classes - np.array of class indices for each box
    #   mask_alpha - transparency level for masks
    # Returns:
    #   image with masks blended on top

    mask_img = image.copy()

    for box, class_id in zip(boxes, classes):
        color = colors[class_id]

        x1, y1, x2, y2 = box.astype(int)

        # Draw filled rectangle (mask) on the mask image
        cv2.rectangle(mask_img, (x1, y1), (x2, y2), color, -1)

    # Blend mask image with original image using alpha blending
    return cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0)
