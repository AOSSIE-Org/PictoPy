import os
import cv2
import shutil
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request


from app.config.settings import DEFAULT_OBJ_DETECTION_MODEL, DEFAULT_FACE_DETECTION_MODEL, IMAGES_PATH
from app.yolov8 import YOLOv8
from app.yolov8.utils import class_names


def get_classes(img_path):
    model_path = DEFAULT_FACE_DETECTION_MODEL
    yolov8_detector = YOLOv8(model_path, conf_thres=0.2, iou_thres=0.3)
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        return None

    # Detect Objects
    print("sleeping..", flush=True)
    time.sleep(5)
    print("woke", flush=True)
    boxes, scores, class_ids = yolov8_detector(img)
    # print(scores, "\n", class_ids)
    # for x in class_ids: print(class_names[x], sep=" ")
    print(f"Inside {class_ids}")
    return {"completed:": f"{class_ids}"}