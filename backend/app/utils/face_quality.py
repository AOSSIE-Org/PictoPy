import cv2
import numpy as np


def face_passes_quality_gate(
    face_crop: np.ndarray,
    bbox: tuple,  # (x1, y1, x2, y2)
    conf_score: float,
    conf_threshold: float,
    blur_threshold: float,
    min_face_size: int,
) -> bool:
    """
    Evaluates a detected face against quality thresholds before it proceeds
    to embedding. All checks must pass for the face to be considered valid.
    """
    # 1. Completeness check (Confidence)
    if conf_score < conf_threshold:
        return False

    # 2. Size check
    x1, y1, x2, y2 = bbox
    area = (x2 - x1) * (y2 - y1)
    if area < min_face_size:
        return False

    # 3. Blur check
    if face_crop.size == 0:
        return False

    if len(face_crop.shape) == 3:
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_crop

    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < blur_threshold:
        return False

    return True
