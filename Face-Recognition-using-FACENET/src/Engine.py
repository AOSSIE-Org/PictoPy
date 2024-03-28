from keras.models import load_model
# imporing necessary libraries
from sklearn.svm import SVC
from sklearn.preprocessing import Normalizer

# importing necessary functions from ML_pipepline
from ML_Pipeline.download_video import download_video
from ML_Pipeline.create_new_folder import create_new_folder
from ML_Pipeline.extracting_frames import extract_frames
from ML_Pipeline.image_modification import loading_images
from ML_Pipeline import embedding_encoding
from ML_Pipeline.facenet_predictions import accuracy
from ML_Pipeline.facenet_predictions import predict
from ML_Pipeline.facenet_predictions import facenet_image_prediction
from ML_Pipeline.facenet_predictions import facenet_video_prediction

# run the following snippet only if video download and extraction of frames has to be done.

# Download video from you tube
# download_video(video_link = "https://www.youtube.com/watch?v=NzOTuh63eVs", path_to_store='../input/video')

# Create new folder to save frames 
# create_new_folder(path = '../input/frames_path')

# Extract frames from video and saving them in frames_path folder
extract_frames(frames_path= '../input/frames_path/', video_file="../input/video/Friends - Monica and Chandlers Wedding.mp4")


# load train dataset
X_train, y_train = loading_images("../input/train/", (160, 160))
X_test, y_test = loading_images("../input/val/", (160, 160))

# loading facenet model
print("Facenet model loaded")
model = load_model('../prebuilt_models/facenet_keras.h5')

# make training dataset
X_train_embedded = embedding_encoding.embedded_array(model, X_train)
X_test_embedded = embedding_encoding.embedded_array(model, X_test)
# Normalizer
l2_encoder = Normalizer(norm='l2')

# normalized embedding vectors
vectorized_data = embedding_encoding.vectorize_vectors(l2_encoder, [X_train_embedded, X_test_embedded])
normalized_train = vectorized_data[0]
normalized_test = vectorized_data[1]

# lable encoded train labels
label_encoder, encoded_train, encoded_test = embedding_encoding.encode_target(y_train, y_test)

# mapping the dictionary for the person name with the lable encoded
label_map = {}
for index, name in enumerate(label_encoder.classes_):
    label_map[index] = name

# fit model
ml_model = SVC(kernel='linear', probability=True)
ml_model.fit(normalized_train, encoded_train)

# prediction on validation data
predicted_val = predict(normalized_test, ml_model)
accuracy_score = accuracy(encoded_test, predicted_val)
print('Accuracy score on validation data is ', accuracy_score)

# Facenet frame prediction
folder = '../input/test_frames/'
size = (160, 160)
output = '../output/'
facenet_image_prediction(folder, output, l2_encoder, ml_model, model, label_map, size)

# Facenet video prediction
print('press Q on keyboard to exit from video window')
video_file_path = '../input/video//Friends - Monica and Chandlers Wedding.mp4'
facenet_video_prediction(video_file_path, l2_encoder, label_map, model, ml_model, size)


