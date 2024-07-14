from app.config.settings import DEFAULT_FACENET_MODEL
from app.facenet.preprocess import normalize_embedding, preprocess_image
import onnxruntime

session = onnxruntime.InferenceSession(DEFAULT_FACENET_MODEL, providers=["CPUExecutionProvider"])

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name

def get_face_embedding(image_path):
    image = preprocess_image(image_path)
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding)


