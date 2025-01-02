import numpy as np
import onnxruntime
from transformers import AutoTokenizer, AutoConfig
import cv2
import asyncio
import time

# Run the ner_onnx.py to create the onnx model in the models folder
def ner_marking(text1):
    # change the path is required
    model_path = r'C:\Users\sanid\Downloads\gsoc_@pictopy\PictoPy\backend\app\models\bert-base-NER.onnx'
    session = onnxruntime.InferenceSession(model_path)

    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    config = AutoConfig.from_pretrained("dslim/bert-base-NER")
    id2label = config.id2label


    def prepare_inputs(text, tokenizer, max_seq_length=32):
        encoding = tokenizer.encode_plus(
            text,
            max_length=max_seq_length,
            truncation=True,
            padding="max_length",
            return_tensors="np"
        )
        
        return {
            "input_ids": encoding["input_ids"].astype(np.int64),
            "attention_mask": encoding["attention_mask"].astype(np.int64),
        }


    def combine_subwords(tokens, labels):
        combined_tokens = []
        combined_labels = []
        current_word = ""
        current_label = None

        for token, label in zip(tokens, labels):
            if token.startswith("##"):
                current_word += token[2:]
            else:
                if current_word:
                    combined_tokens.append(current_word)
                    combined_labels.append(current_label)
                current_word = token
                current_label = label

        if current_word:
            combined_tokens.append(current_word)
            combined_labels.append(current_label)

        return combined_tokens, combined_labels


    def perform_ner(text, session, tokenizer, id2label):

        inputs = prepare_inputs(text, tokenizer)
        
    
        outputs = session.run(
            None,
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            },
        )

        logits = outputs[0]
        predictions = np.argmax(logits, axis=-1)

        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        filtered_tokens = []
        filtered_labels = []

        for token, pred in zip(tokens, predictions[0]):
            label = id2label[pred]
            if token not in ["[PAD]", "[CLS]", "[SEP]"]:
                filtered_tokens.append(token)
                filtered_labels.append(label)

        combined_tokens, combined_labels = combine_subwords(filtered_tokens, filtered_labels)
        return list(zip(combined_tokens, combined_labels))


    def compare_ner_results(text1, session, tokenizer, id2label):

        ner_result1 = perform_ner(text1, session, tokenizer, id2label)
    

        
        ner_dict1 = {token: label for token, label in ner_result1 if label != 'O'}
        ner_list = [token for token in ner_dict1.keys()]
        

        print("Original NER Results:")
        for token, label in ner_result1:
            print(f"{token:15} -> {label}")
        print(ner_dict1)
        return ner_list


    return compare_ner_results(text1, session, tokenizer, id2label)
    
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

#change the path if required
session = onnxruntime.InferenceSession(
    r'C:\Users\sanid\Downloads\gsoc_@pictopy\PictoPy\backend\app\models\facenet.onnx', providers=["CPUExecutionProvider"]
)

input_tensor_name = session.get_inputs()[0].name
output_tensor_name = session.get_outputs()[0].name   

def normalize_embedding(embedding):
    return embedding / np.linalg.norm(embedding)

def get_face_embeddings(image):
    result = session.run([output_tensor_name], {input_tensor_name: image})[0]
    embedding = result[0]
    return normalize_embedding(embedding)      

def scanned_embeddings(name): 
    text_to_display = ner_marking(name)  
    print(f"Text to Display: {text_to_display}")

    #change the path if required
    face_cascade = cv2.CascadeClassifier(r'C:\Users\sanid\Downloads\gsoc_@pictopy\PictoPy\backend\app\ner\haarcascade_frontalface_default.xml')
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
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, f"Enter to Capture", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, names, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow("Face Embedding Scanner", frame)

            if cv2.waitKey(1) & 0xFF == 13: 
                try:
                    time.sleep(2)
                    if len(faces) == 0:
                        print("no face detected")
                        return
                    else:    
                        face = frame[y:y + h, x:x + w]
                        face = face.astype(np.float32)
                        preprocessed_face = preprocess_face_for_onnx(face)
                        embedding_vector = get_face_embeddings(preprocessed_face) 
                        print(f"Captured embedding for {names}: {embedding_vector}")
                        return 
                except Exception as e:
                    print(f"Error capturing embedding: {e}")
                    return
    
    for names in text_to_display:
        scanning(names)
        time.sleep(2)  

    cap.release()
    cv2.destroyAllWindows()

    return {"status": "processing completed"}

if __name__ == "__main__":
    scanned_embeddings("Aryan and Baldwin")
