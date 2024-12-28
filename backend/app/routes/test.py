import os
import cv2
import shutil
import asyncio
from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL, DEFAULT_FACE_DETECTION_MODEL, IMAGES_PATH
from app.yolov8 import YOLOv8
from app.yolov8.utils import class_names
from app.utils.classification import get_classes

router = APIRouter()

async def run_get_classes(img_path):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    print(result)

@router.post("/return")
async def test_route(payload: dict):
    try:
        model_path = DEFAULT_FACE_DETECTION_MODEL
        yolov8_detector = YOLOv8(model_path, conf_thres=0.2, iou_thres=0.3)
        print(payload)
        
        if 'path' not in payload:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Missing 'path' in payload",
                        "message": "Image path is required"
                    }
                }
            )
        
        img_path = payload['path']
        img = cv2.imread(img_path)

        if img is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Failed to load image",
                        "message": f"Failed to load image: {img_path}"
                    }
                }
            )

        boxes, scores, class_ids = yolov8_detector(img)
        print(scores, "\n", class_ids)
        detected_classes = [class_names[x] for x in class_ids]
        
        asyncio.create_task(run_get_classes(img_path))
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": {
                    "class_ids": class_ids.tolist(),
                    "detected_classes": detected_classes
                },
                "message": "Object detection completed successfully",
                "success": True
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.get("/images")
def get_images():
    try:
        files = os.listdir(IMAGES_PATH)
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] 
        image_files = [os.path.abspath(os.path.join(IMAGES_PATH, file)) for file in files if os.path.splitext(file)[1].lower() in image_extensions]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": {"images": image_files},
                "message": "Successfully retrieved all images",
                "success": True
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.post("/single-image")
def add_single_image(payload: dict):
    try:
        if 'path' not in payload:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Missing 'path' in payload",
                        "message": "Image path is required"
                    }
                }
            )

        image_path = payload['path']
        if not os.path.isfile(image_path):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Invalid file path",
                        "message": "The provided path is not a valid file"
                    }
                }
            )

        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension not in image_extensions:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Invalid file type",
                        "message": "The file is not a supported image type"
                    }
                }
            )

        destination_path = os.path.join(IMAGES_PATH, os.path.basename(image_path))
        shutil.copy(image_path, destination_path)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": {"destination_path": destination_path},
                "message": "Image copied to the gallery successfully",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )