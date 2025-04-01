import numpy as np
import cv2
from typing import List, Tuple, cast

class_names: List[str] = [
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

rng = np.random.default_rng(3)
colors: np.ndarray = rng.uniform(0, 255, size=(len(class_names), 3))


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
    sorted_indices: np.ndarray = np.argsort(scores)[::-1]

    keep_boxes: List[int] = []
    while sorted_indices.size > 0:
        box_id: int = sorted_indices[0]
        keep_boxes.append(box_id)

        ious: np.ndarray = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        keep_indices: np.ndarray = np.where(ious < iou_threshold)[0]
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def multiclass_nms(
    boxes: np.ndarray, scores: np.ndarray, class_ids: np.ndarray, iou_threshold: float
) -> List[int]:
    unique_class_ids: np.ndarray = np.unique(class_ids)

    keep_boxes: List[int] = []
    for class_id in unique_class_ids:
        class_indices: np.ndarray = np.where(class_ids == class_id)[0]
        class_boxes: np.ndarray = boxes[class_indices, :]
        class_scores: np.ndarray = scores[class_indices]

        class_keep_boxes: List[int] = nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def compute_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    xmin: np.ndarray = np.maximum(box[0], boxes[:, 0])
    ymin: np.ndarray = np.maximum(box[1], boxes[:, 1])
    xmax: np.ndarray = np.minimum(box[2], boxes[:, 2])
    ymax: np.ndarray = np.minimum(box[3], boxes[:, 3])

    intersection_area: np.ndarray = np.maximum(0, xmax - xmin) * np.maximum(
        0, ymax - ymin
    )

    box_area: float = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area: np.ndarray = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area: np.ndarray = box_area + boxes_area - intersection_area

    iou: np.ndarray = intersection_area / union_area
    return iou


def xywh2xyxy(x: np.ndarray) -> np.ndarray:
    y: np.ndarray = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def draw_detections(
    image: np.ndarray,
    boxes: np.ndarray,
    scores: np.ndarray,
    class_ids: np.ndarray,
    mask_alpha: float = 0.3,
    confidence_threshold: float = 0.3,
) -> np.ndarray:
    det_img: np.ndarray = image.copy()

    img_height, img_width = image.shape[:2]
    font_size: float = min([img_height, img_width]) * 0.0006
    text_thickness: int = int(min([img_height, img_width]) * 0.001)

    det_img = draw_masks(det_img, boxes, class_ids, mask_alpha)

    for class_id, box, score in zip(class_ids, boxes, scores):
        if score < confidence_threshold or class_id >= len(class_names) - 1:
            color: np.ndarray = colors[-1]
            label: str = "unknown"
        else:
            color = colors[class_id]
            label = class_names[class_id]

        draw_box(det_img, box, tuple(color.astype(int)))
        caption: str = f"{label} {int(score * 100)}%"
        draw_text(
            det_img, caption, box, tuple(color.astype(int)), font_size, text_thickness
        )

    return det_img


def draw_box(
    image: np.ndarray,
    box: np.ndarray,
    color: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
) -> np.ndarray:
    x1, y1, x2, y2 = box.astype(int)
    return cast(np.ndarray, cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness))


def draw_text(
    image: np.ndarray,
    text: str,
    box: np.ndarray,
    color: Tuple[int, int, int] = (0, 0, 255),
    font_size: float = 0.001,
    text_thickness: int = 2,
) -> np.ndarray:
    x1, y1, _, _ = box.astype(int)
    (tw, th), _ = cv2.getTextSize(
        text=text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_size,
        thickness=text_thickness,
    )
    th = int(th * 1.2)

    cv2.rectangle(image, (x1, y1), (x1 + tw, y1 - th), color, -1)

    return cast(
        np.ndarray,
        cv2.putText(
            image,
            text,
            (x1, y1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_size,
            (255, 255, 255),
            text_thickness,
            cv2.LINE_AA,
        ),
    )


def draw_masks(
    image: np.ndarray, boxes: np.ndarray, classes: np.ndarray, mask_alpha: float = 0.3
) -> np.ndarray:
    mask_img: np.ndarray = image.copy()

    for box, class_id in zip(boxes, classes):
        color: np.ndarray = colors[class_id]
        x1, y1, x2, y2 = box.astype(int)
        cv2.rectangle(mask_img, (x1, y1), (x2, y2), color.tolist(), -1)

    return cast(
        np.ndarray,
        cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0),
    )
