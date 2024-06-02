import os
import cv2
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, Request


from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL, DEFAULT_FACE_DETECTION_MODEL, IMAGES_PATH
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


@router.get("/images")
def get_images():
    try:
        files = os.listdir(IMAGES_PATH)
        # for now include bmp and gif, could remove later
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] 
        image_files = [os.path.abspath(os.path.join(IMAGES_PATH, file)) for file in files if os.path.splitext(file)[1].lower() in image_extensions]
        
        return {"images": image_files}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    


@router.post("/single-image")
def add_single_image(payload: dict):
    try:
        if 'path' not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'path' in payload")

        image_path = payload['path']
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")

        # for now include bmp and gif, could remove later
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension not in image_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not an image")

        destination_path = os.path.join(IMAGES_PATH, os.path.basename(image_path))
        # if we do not want to store copies and just move use shutil.move instead
        shutil.copy(image_path, destination_path)

        return {"message": "Image copied to the gallery successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))