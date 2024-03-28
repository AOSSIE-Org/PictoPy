import numpy as np
from numpy import asarray, expand_dims
from sklearn.preprocessing import LabelEncoder


# This function is used to predict 1D 128 vector embeddings from a pre-trained facenet model

def embedding_generation_from_facenet(model, pixels):
    pixels = pixels.astype('float32')
    pixels_mean = np.mean(pixels)
    pixels_deviation = np.std(pixels)
    normalized_pixels = (pixels - pixels_mean) / pixels_deviation
    transformed_pixel = expand_dims(normalized_pixels, axis=0)
    embeddings = model.predict(transformed_pixel)

    return embeddings[0]


# This function is used to get embeddings from each face pixels from a training set

def embedded_array(model, array_data):
    embedding_list = []
    for face_pixels in array_data:
        embedding = embedding_generation_from_facenet(model, face_pixels)
        embedding_list.append(embedding)
    embedding_list = asarray(embedding_list)
    return embedding_list


# This function is used to normalize the embedding vectors

def vectorize_vectors(encoder, dataX):
    normalized_data = []
    for data_x in dataX:
        normalized_data.append(encoder.transform(data_x))

    return normalized_data


# This function is used to label encode the train and test labels

def encode_target(datay1, datay2):
    label_encoder = LabelEncoder()
    label_encoder.fit(datay1)
    datay1_train = label_encoder.transform(datay1)
    datay2_test = label_encoder.transform(datay2)

    return label_encoder, datay1_train, datay2_test