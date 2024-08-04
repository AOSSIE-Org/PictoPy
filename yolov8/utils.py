import numpy as np
import cv2
class_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
               'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
               'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
               'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
               'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard',
               'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
               'scissors', 'teddy bear', 'hair drier', 'toothbrush']

# Create a list of colors for each class where each color is a list of 3 integer values
rng = np.random.default_rng(3)
colors = rng.uniform(0, 255, size=(len(class_names), 3))


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> np.ndarray:
    """
    Performs non-maximum suppression (NMS) on a set of bounding boxes.

    Args:
        boxes: A numpy array of bounding boxes in the format (x1, y1, x2, y2).
        scores: A numpy array of scores for each bounding box.
        iou_threshold: The IoU threshold for suppression.

    Returns:
        A numpy array of indices of the kept boxes.
    """

    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the last box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of the picked box with the rest
        ious = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]

        # print(keep_indices.shape, sorted_indices.shape)
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def multiclass_nms(boxes: np.ndarray, scores: np.ndarray, class_ids: np.ndarray, iou_threshold: float) -> np.ndarray:
    """
    Performs multi-class non-maximum suppression (NMS) on a set of bounding boxes.

    Args:
        boxes: A numpy array of bounding boxes in the format (x1, y1, x2, y2).
        scores: A numpy array of scores for each bounding box.
        class_ids: A numpy array of class IDs for each bounding box.
        iou_threshold: The IoU threshold for suppression.

    Returns:
        A numpy array of indices of the kept boxes.
    """

    unique_class_ids = np.unique(class_ids)

    keep_boxes = []
    for class_id in unique_class_ids:
        class_indices = np.where(class_ids == class_id)[0]
        class_boxes = boxes[class_indices,:]
        class_scores = scores[class_indices]

        class_keep_boxes = nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def compute_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """
    Computes the Intersection over Union (IoU) between a bounding box and a set of bounding boxes.

    Args:
        box: A numpy array of a single bounding box in the format (x1, y1, x2, y2).
        boxes: A numpy array of bounding boxes in the format (x1, y1, x2, y2).

    Returns:
        A numpy array of IoU values between the input box and each box in the set.
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

def xywh2xyxy(x: np.ndarray) -> np.ndarray:
    """
    Converts bounding boxes from (x, y, w, h) format to (x1, y1, x2, y2) format.

    Args:
        x: A numpy array of bounding boxes in (x, y, w, h) format.

    Returns:
        A numpy array of bounding boxes in (x1, y1, x2, y2) format.
    """
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def draw_detections(image: np.ndarray, boxes: np.ndarray, scores: np.ndarray, class_ids: np.ndarray, mask_alpha: float = 0.3) -> np.ndarray:
    """
    Draws detections on an image.

    Args:
        image: The image to draw detections on.
        boxes: A numpy array of bounding boxes in (x1, y1, x2, y2) format.
        scores: A numpy array of detection scores.
        class_ids: A numpy array of class IDs.
        mask_alpha: The alpha value for the mask.

    Returns:
        The image with detections drawn on it.
    """
    det_img = image.copy()

    img_height, img_width = image.shape[:2]
    font_size = min([img_height, img_width]) * 0.0006
    text_thickness = int(min([img_height, img_width]) * 0.001)

    det_img = draw_masks(det_img, boxes, class_ids, mask_alpha)

    # Draw bounding boxes and labels of detections
    for class_id, box, score in zip(class_ids, boxes, scores):

        color = colors[class_id]

        draw_box(det_img, box, color)

        label = class_names[class_id]
        caption = f'{label} {int(score * 100)}%'
        draw_text(det_img, caption, box, color, font_size, text_thickness)

    return det_img

def draw_box( image: np.ndarray, box: np.ndarray, color: list[int, int, int] = (0, 0, 255),
             thickness: int = 2) -> np.ndarray:
    """
    Draws a rectangle on the image with the specified color and thickness.

    Args:
        image: The image to draw on.
        box: A numpy array of the bounding box in the format (x1, y1, x2, y2).
        color: The color of the rectangle.
        thickness: The thickness of the rectangle.

    Returns:
        The image with the rectangle drawn on it.
    """
    x1, y1, x2, y2 = box.astype(int)
    return cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)


def draw_text(image: np.ndarray, text: str, box: np.ndarray, color: list[int, int, int] = (0, 0, 255),
              font_size: float = 0.001, text_thickness: int = 2) -> np.ndarray:
    """
    Draws text on the image at the specified location with the specified color, font size, and thickness.

    Args:
        image: The image to draw on.
        text: The text to draw.
        box: A numpy array of the bounding box in the format (x1, y1, x2, y2).
        color: The color of the text.
        font_size: The font size of the text.
        text_thickness: The thickness of the text.

    Returns:
        The image with the text drawn on it.
    """
    x1, y1, x2, y2 = box.astype(int)
    (tw, th), _ = cv2.getTextSize(text=text, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                  fontScale=font_size, thickness=text_thickness)
    th = int(th * 1.2)

    cv2.rectangle(image, (x1, y1),
                  (x1 + tw, y1 - th), color, -1)

    return cv2.putText(image, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255), text_thickness, cv2.LINE_AA)

def draw_masks(image: np.ndarray, boxes: np.ndarray, classes: np.ndarray, mask_alpha: float = 0.3) -> np.ndarray:
    """
    Draws masks on the image for the specified bounding boxes and classes.

    Args:
        image: The image to draw on.
        boxes: A numpy array of bounding boxes in the format (x1, y1, x2, y2).
        classes: A numpy array of class IDs.
        mask_alpha: The alpha value for the masks.

    Returns:
        The image with the masks drawn on it.
    """
    mask_img = image.copy()

    # Draw bounding boxes and labels of detections
    for box, class_id in zip(boxes, classes):
        color = colors[class_id]

        x1, y1, x2, y2 = box.astype(int)

        # Draw fill rectangle in mask image

        cv2.rectangle(mask_img, (x1, y1), (x2, y2), color, -1)

    return cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0)
