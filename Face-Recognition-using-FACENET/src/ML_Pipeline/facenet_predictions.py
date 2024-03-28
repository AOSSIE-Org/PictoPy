# importing necessary libraries
import numpy as np
import cv2
from numpy import asarray
from skimage.transform import resize
from os import listdir
from sklearn.metrics import accuracy_score

# importing necessary functions from ML_pipeline
from src.ML_Pipeline import image_modification
from src.ML_Pipeline import embedding_encoding


# Function to predict faces in images by using Facenet model
def facenet_image_prediction(frames_folder, output_path, l2_encoder, ml_model, model, label_map, size=(160, 160)):
    print('Prediction on frames by Facenet model is started')
    for filename in listdir(frames_folder):

        frame_path = frames_folder + filename
        image, faces = image_modification.face_extarct_using_CV(frame_path)
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            roi_color = image[y:y + h, x:x + w]
            res_img = resize(roi_color, size)
            pixels = asarray(res_img)
            embed = embedding_encoding.embedding_generation_from_facenet(model, pixels)
            norm_vec = l2_encoder.transform(np.expand_dims(embed, axis=0))
            per_prob = ml_model.predict_proba(norm_vec)[0]
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if np.max(per_prob) >= 0.5:
                name = label_map[np.argmax(per_prob)]
                img = cv2.putText(image, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 2, cv2.LINE_AA)
            else:
                img = cv2.putText(image, 'others', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 2,
                                  cv2.LINE_AA)

        cv2.imwrite(output_path + frame_path.split('/')[-1].split('.')[0] + '_facenet_pred.jpg', image)
    print('Predicted frames are stored in ', output_path, 'folder')
    print('Prediction on frames ended!')


# Function to predict faces in video by using Facenet model
def facenet_video_prediction(video_file, l2_encoder, label_map, model, ml_model, size=(160, 160)):
    print('Prediction on video by Facenet model is started')
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    video_object = cv2.VideoCapture(video_file)
    if (video_object.isOpened() == False):
        print("Error opening video  file")

    while (video_object.isOpened()):

        content, frame = video_object.read()
        if content == True:
            color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = faceCascade.detectMultiScale(
                color,
                scaleFactor=1.2,
                minNeighbors=10,
                minSize=(64, 64),
                flags=cv2.cv2.CASCADE_SCALE_IMAGE
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                roi_color = frame[y:y + h, x:x + w]
                res_img = resize(roi_color, size)
                pixels = asarray(res_img)
                embed = embedding_encoding.embedding_generation_from_facenet(model, pixels)
                norm_vec = l2_encoder.transform(np.expand_dims(embed, axis=0))
                per_prob = ml_model.predict_proba(norm_vec)[0]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if np.max(per_prob) >= 0.5:
                    name = label_map[np.argmax(per_prob)]
                    img = cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 2,
                                      cv2.LINE_AA)

                else:
                    img = cv2.putText(frame, 'others', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 2,
                                      cv2.LINE_AA)

            cv2.imshow('Video', frame)

            # Press Q on keyboard to  exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        else:
            break

    # the video capture object
    video_object.release()
    print('Prediction on video ended!')
    cv2.destroyAllWindows()


# Function to predict on test data and calculating the accuracy
def predict(data, model):
    prediction = model.predict(data)
    return prediction


# Function to calculate the accuracy
def accuracy(test_data, predicted_data):
    accuracy = accuracy_score(test_data, predicted_data)
    return accuracy
