import pytest
from fastapi import HTTPException

from app.models.FaceDetector import FaceDetector
from app.models.YOLO import YOLO
from app.models.ObjectClassifier import ObjectClassifier


def test_invalid_image_face_detector():
    detector = FaceDetector()
    with pytest.raises(HTTPException):
        detector.detect_faces("1", "fake_image.jpg")


def test_invalid_image_yolo():
    yolo = YOLO("models/yolo11n_face.onnx")
    with pytest.raises(HTTPException):
        yolo("fake_image.jpg")   # if YOLO takes a path, adjust accordingly


def test_invalid_image_object_classifier():
    classifier = ObjectClassifier("models/yolo11n_general.onnx")
    with pytest.raises(HTTPException):
        classifier("fake_image.jpg")
