import os
import cv2
import math
from math import floor


def extract_frames(frames_path, video_file):
    if len(os.listdir(frames_path)) == 0:
        count = 0
        video_object = cv2.VideoCapture(video_file)
        rate_of_frame = video_object.get(5)  # Each second frame

        while (video_object.isOpened()):
            frame_id = video_object.get(1)
            content, frame = video_object.read()
            if (content != True):
                break
            if (frame_id % floor(rate_of_frame) == 0):
                filename = "frame%d.jpg" % count
                count += 1
                cv2.imwrite(frames_path + filename, frame)

        video_object.release()
        print("Done!", count)


def face_extrct_using_cv(path):
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    image = cv2.imread(path)
    color = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faces = faceCascade.detectMultiScale(color,
                                         scaleFactor=1.2,
                                         minNeighbors=10,
                                         minSize=(64, 64),
                                         flags=cv2.CASCADE_SCALE_IMAGE)

    return image, faces
