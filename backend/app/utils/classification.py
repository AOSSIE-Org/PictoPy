import cv2
from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL
from app.yolov8 import YOLOv8


def get_classes(img_path):
    yolov8_detector = YOLOv8(DEFAULT_OBJ_DETECTION_MODEL, conf_thres=0.2, iou_thres=0.3)
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    _, _, class_ids = yolov8_detector(img)
    id_str = [str(x) for x in class_ids]
    id_str = ','.join(id_str)
    print(id_str, flush=True)
    return id_str
