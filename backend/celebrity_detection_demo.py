import cv2
import numpy as np
import os
import sys

# Ensure backend directory is in python path to allow imports from app.*
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)  # Insert at the beginning to avoid conflicts

# We don't need the parent directory if we are running from backend and 'app' is inside backend
# Removing parent_dir addition to avoid conflict with root's app.py

try:
    from app.models.FaceDetector import FaceDetector
    from app.models.FaceNet import FaceNet
    from app.models.CelebrityMatcher import CelebrityMatcher
    from app.utils.FaceNet import FaceNet_util_preprocess_image
    from app.logging.setup_logging import get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please make sure you are running this script from the backend directory or with the correct PYTHONPATH.")
    sys.exit(1)

# Initialize logger (optional for demo script but good practice)
logger = get_logger(__name__)

def run_celebrity_detection_demo(image_path):
    print(f"--- Starting Celebrity Detection on {image_path} ---")

    # 1. Initialize Models
    print("Initializing models...")
    try:
        # Note: FaceDetector initializes its own FaceNet internally, but for this custom pipeline 
        # as requested, we might want to use individual components if FaceDetector is too coupled.
        # However, FaceDetector.yolo_detector is accessible.
        face_detector = FaceDetector()
        
        # We need a separate FaceNet instance for our explicit embedding step 
        # if we don't want to use face_detector internals,
        # OR we can reuse face_detector.facenet if it exposes what we need.
        # FaceDetector has self.facenet. 
        facenet = face_detector.facenet
        
        # Use default path (rel to CelebrityMatcher file)
        celebrity_matcher = CelebrityMatcher()
        
    except Exception as e:
        print(f"Failed to initialize models: {e}")
        return

    # 2. Load Image
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return

    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image from {image_path}")
        return

    # 3. Detect Faces
    # Using the YOLO detector inside FaceDetector as requested ("Use FaceDetector to find face bounding boxes")
    # FaceDetector.detect_faces() does everything, but we want to demonstrate the pipeline steps.
    # So we access the underlying YOLO detector.
    print("Detecting faces...")
    # The yolo_detector call returns boxes, scores, class_ids
    boxes, scores, class_ids = face_detector.yolo_detector(img)

    if len(boxes) == 0:
        print("No faces detected.")
        return

    print(f"Found {len(boxes)} faces.")

    # 4. Process Each Face
    for i, (box, score) in enumerate(zip(boxes, scores)):
        # Filter by confidence if needed (YOLO class usually handles this internally or returns all)
        # FaceDetector uses 0.45 threshold.
        if score < face_detector.yolo_detector.conf_threshold:
            continue

        x1, y1, x2, y2 = map(int, box)
        print(f"Processing Face {i+1} at [{x1}, {y1}, {x2}, {y2}]...")

        # Crop Face (with some padding like FaceDetector does)
        padding = 20
        h, w, _ = img.shape
        face_img = img[
            max(0, y1 - padding) : min(h, y2 + padding),
            max(0, x1 - padding) : min(w, x2 + padding)
        ]

        if face_img.size == 0:
            print("Empty crop, skipping.")
            continue

        # 5. Preprocess for FaceNet (Resize to 160x160)
        # The user requested: "preprocess it (resize to 160x160)"
        # FaceNet_util_preprocess_image handles: Resize -> RGB -> Transpose -> ExpandDims -> Normalize
        # We'll use the util to ensure compatibility with the model.
        # If manual resize is strictly required separately:
        # resized_face = cv2.resize(face_img, (160, 160)) 
        # preprocessed_face = FaceNet_util_preprocess_image_from_resized(resized_face) 
        # But FaceNet_util_preprocess_image includes the resize, so we use it directly.
        
        try:
            # FaceNet expects the processed tensor
            preprocessed_face = FaceNet_util_preprocess_image(face_img)
            
            # 6. Get Embedding
            embedding = facenet.get_embedding(preprocessed_face)

            # 7. Match Celebrity
            name = celebrity_matcher.identify_face(embedding)

            if name:
                print(f"Result: Found {name} at [{x1}, {y1}, {x2}, {y2}]")
                # Optional: specific logging format
            else:
                print(f"Result: Unknown person at [{x1}, {y1}, {x2}, {y2}]")
                
        except Exception as e:
            print(f"Error processing face {i+1}: {e}")

    print("--- Scanning Complete ---")

if __name__ == "__main__":
    # Example usage
    # You can pass an image path as an argument
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
    else:
        # Default or dummy path for demonstration
        target_image = "tests/inputs/sample_celebrity.jpg" # Adjust as needed
    
    run_celebrity_detection_demo(target_image)
