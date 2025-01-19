import cv2
from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL
from app.yolov8 import YOLOv8


def get_classes(img_path):
    yolov8_detector = YOLOv8(DEFAULT_OBJ_DETECTION_MODEL, conf_thres=0.4, iou_thres=0.5)
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    boxes, scores, class_ids = yolov8_detector(img)
    
    # Process class IDs to handle unknown classes
    processed_class_ids = []
    for class_id in class_ids:
        if class_id < 0 or class_id >= yolov8_detector.num_classes:
            processed_class_ids.append(yolov8_detector.num_classes)  # Assign 'unknown' class ID
        else:
            processed_class_ids.append(class_id)
    id_str = ','.join(str(x) for x in processed_class_ids)
    print(id_str, flush=True)
    return id_str
