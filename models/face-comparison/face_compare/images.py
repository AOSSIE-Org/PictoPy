'''Module containing image helper functions'''
import cv2


def get_face(img):
    '''Crops image to only include face plus a border'''
    height, width, _ = img.shape
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    face_box = face_cascade.detectMultiScale(img)
    # Get dimensions of bounding box
    x, y, w, h = tuple(map(tuple, face_box))[0]
    # Calculate padding as segmentation is too tight.
    pad_w = int(w / 2.5)
    pad_h = int(h / 2.5)
    # Get co-ordinates of crop
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(width, x + w + pad_w)
    y2 = min(height, y + h + pad_h)
    # Crop image
    cropped = img[y1:y2, x1:x2]
    return cropped
