import numpy as np
import cv2
import numpy as np
import onnxruntime
from app.config.settings import DEFAULT_FRONTAL_MODEL,DEFAULT_FACENET_MODEL
import cv2
import asyncio
from numpy.linalg import norm
import time

def preprocess_face_for_onnx(face_image):
    """
    Preprocess the face image before passing it to the ONNX model.
    
    Args:
        face_image (numpy.ndarray): A cropped image containing a single face.
        
    Returns:
        numpy.ndarray: Preprocessed image ready for the ONNX model.
    """

    resized_face = cv2.resize(face_image, (160, 160))
    
    rgb_face = resized_face[:, :, ::-1]  
   
    normalized_face = rgb_face.astype(np.float32) / 255.0
    
  

    preprocessed_face = np.expand_dims(normalized_face, axis=0)  
   
    preprocessed_face = np.transpose(preprocessed_face, (0, 3, 1, 2)) 
    
    return preprocessed_face   

session = onnxruntime.InferenceSession(
    DEFAULT_FACENET_MODEL, providers=["CPUExecutionProvider"]
)

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name   

def normalize_embedding(embedding):
    return embedding / np.linalg.norm(embedding)

def brightness(img):
    if len(img.shape) == 3:
        # Colored RGB or BGR (*Do Not* use HSV images with this function)
        # create brightness with euclidean norm
        return np.average(norm(img, axis=2)) / np.sqrt(3)
    else:
        # Grayscale
        return np.average(img)

def get_face_embeddings(image):
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding) 


def scanned_embeddings(name): 

    face_cascade = cv2.CascadeClassifier(DEFAULT_FRONTAL_MODEL)
    if face_cascade.empty():
        raise FileNotFoundError("Failed to load Haar cascade file. Check the file path.")

    cap = cv2.VideoCapture(0)

    def scanning(names):
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                face = frame[y:y + h, x:x + w]
                face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                mean_brightness = brightness(face_gray)

                # Add messages for brightness issues
                if mean_brightness < 60:
                    cv2.putText(frame, f"Brightness too low! ({int(mean_brightness)})", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2, cv2.LINE_AA)
                if mean_brightness > 150:
                    cv2.putText(frame, f"Brightness too high! ({int(mean_brightness)})", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2, cv2.LINE_AA)
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, f"Enter to Capture", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, names, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow("Face Embedding Scanner", frame)

            if cv2.waitKey(1) & 0xFF == 13:  
                try:
                    time.sleep(2)
                    if len(faces) == 0:
                        print("No face detected. Please try again.")
                        return
                    
                    face = frame[y:y + h, x:x + w]
                    face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                    mean_brightness = np.mean(face_gray)
                    
                    if mean_brightness < 50 or mean_brightness > 200:
                        print("Brightness is not optimal. Please adjust the lighting.")
                        return
                    
                    face = face.astype(np.float32)
                    preprocessed_face = preprocess_face_for_onnx(face)
                    embedding_vector = get_face_embeddings(preprocessed_face) 
                    print(f"Captured embedding for {names}: {embedding_vector}")
                    return embedding_vector

                except Exception as e:
                    print(f"Error capturing embedding: {e}")
                    return
    
    embedding_vector = scanning(name)
    time.sleep(2)  

    cap.release()
    cv2.destroyAllWindows()

    return embedding_vector