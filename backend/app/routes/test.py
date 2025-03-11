import cv2
import asyncio
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config.settings import DEFAULT_FACE_DETECTION_MODEL
from app.yolov8 import YOLOv8
from app.yolov8.utils import class_names
from app.utils.classification import get_classes
from app.routes.images import get_all_image_paths

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

        if "path" not in payload:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Missing 'path' in payload",
                        "message": "Image path is required",
                    },
                },
            )

        img_path = payload["path"]
        img = cv2.imread(img_path)

        if img is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "content": {
                        "success": False,
                        "error": "Failed to load image",
                        "message": f"Failed to load image: {img_path}",
                    },
                },
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
                    "detected_classes": detected_classes,
                },
                "message": "Object detection completed successfully",
                "success": True,
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e),
                },
            },
        )


@router.get("/images")
def get_images():
    try:
        image_files = get_all_image_paths()

        return JSONResponse(
            status_code=200,
            content={
                "data": {"image_files": image_files},
                "message": "Successfully retrieved all images",
                "success": True,
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "message": str(e),
            },
        )
