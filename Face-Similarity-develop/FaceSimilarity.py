# face verification with the VGGFace2 model
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from scipy.spatial.distance import cosine
from mtcnn.mtcnn import MTCNN
from utils import preprocess_input
from vggface import VGGFace
import sys


# extract a single face from a given photograph
def extract_face(filename, required_size=(224, 224)):
    img = plt.imread(filename)
    detector = MTCNN()
    results = detector.detect_faces(img)
    x1, y1, width, height = results[0]['box']
    x2, y2 = x1 + width, y1 + height
    # extract the face
    face = img[y1:y2, x1:x2]
    # resize pixels to the model size
    image = Image.fromarray(face)
    image = image.resize(required_size)
    face_array = np.asarray(image)
    return face_array


# extract faces and calculate face embeddings for a list of photo files
def get_embeddings(filenames):
    # extract faces
    faces = [extract_face(f) for f in filenames]
    # convert into an array of samples
    samples = np.asarray(faces, 'float32')
    # prepare the face for the model, e.g. center pixels
    samples = preprocess_input(samples, version=2)

    model = VGGFace(model='resnet50', include_top=False, input_shape=(224, 224, 3), pooling='avg')
    pred = model.predict(samples)
    return pred


# determine if a candidate face is a match for a known face
def is_match(known_embedding, candidate_embedding, thresh=0.5):
    # calculate distance between embeddings
    score = cosine(known_embedding, candidate_embedding)

    print('*****************************************************************')
    print('Threshold for the face similarity score is 0.5')

    if score <= thresh:
        print('Face is a Match with score of %.3f' % score)
    else:
        print('Face is not a Match with score of %.3f' % score)

    print('********************************************************************')


def main():
    embeddings = get_embeddings([sys.argv[1], sys.argv[2]])
    is_match(embeddings[0], embeddings[1])


if __name__ == '__main__':
    main()
