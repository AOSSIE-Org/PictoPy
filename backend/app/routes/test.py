from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL, DEFAULT_FACE_DETECTION_MODEL
import cv2
from app.yolov8 import YOLOv8
from app.yolov8.utils import class_names

router = APIRouter()


@router.post("/return")
def test_route(payload: dict):
    model_path = DEFAULT_FACE_DETECTION_MODEL
    yolov8_detector = YOLOv8(model_path, conf_thres=0.2, iou_thres=0.3)
    print(payload)
    # Read local image file
    img_path = payload['path']
    img = cv2.imread(img_path)

    # Check if the image was loaded successfully
    if img is None:
        print(f"Failed to load image: {img_path}")
        exit()

    # Detect Objects
    boxes, scores, class_ids = yolov8_detector(img)
    print(scores, "\n", class_ids)
    for x in class_ids: print(class_names[x], sep=" ")
    # Draw detections
    combined_img = yolov8_detector.draw_detections(img)
    cv2.namedWindow("Detected Objects", cv2.WINDOW_NORMAL)
    cv2.imshow("Detected Objects", combined_img)
    cv2.imwrite("tests/outputs/detected_objects.jpg", combined_img)

    # Wait for a key press or window close event
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.getWindowProperty("Detected Objects", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Clean up
    cv2.destroyAllWindows()
    return {"message": f"{class_ids}"}
