"""
Face Detection and Recognition Module

This module provides the FaceDetector class which combines YOLO-based face detection
with FaceNet-based face recognition to identify and extract face embeddings from images.

The FaceDetector performs the following operations:
1. Uses YOLO to detect faces in images
2. Extracts face regions with padding
3. Uses FaceNet to generate face embeddings
4. Stores face data in the database for clustering and recognition

Key Features:
- Configurable confidence and IoU thresholds
- Automatic face region extraction with padding
- Face embedding generation for similarity matching
- Database integration for face data persistence
"""

# Standard library imports
import cv2
from app.models.FaceNet import FaceNet
from app.utils.FaceNet import FaceNet_util_preprocess_image, FaceNet_util_get_model_path
from app.utils.YOLO import YOLO_util_get_model_path
from app.models.YOLO import YOLO
from app.database.faces import db_insert_face_embeddings_by_image_id


class FaceDetector:
    """
    Face detection and recognition system using YOLO and FaceNet.
    
    This class combines YOLO-based face detection with FaceNet-based face recognition
    to identify faces in images and generate embeddings for face clustering and recognition.
    """
    
    def __init__(self):
        """
        Initialize the FaceDetector with YOLO and FaceNet models.
        
        Sets up the YOLO face detector with optimized thresholds and initializes
        the FaceNet model for face embedding generation.
        """
        # Initialize YOLO face detector with optimized thresholds
        self.yolo_detector = YOLO(
            YOLO_util_get_model_path("face"),  # Get face-specific YOLO model
            conf_threshold=0.35,               # Confidence threshold for face detection
            iou_threshold=0.45,                # IoU threshold for non-maximum suppression
        )
        
        # Initialize FaceNet model for face embedding generation
        self.facenet = FaceNet(FaceNet_util_get_model_path())
        
        # Mark as initialized
        self._initialized = True
        print("FaceDetector initialized with YOLO and FaceNet models.")

    def detect_faces(self, image_id: int, image_path: str):
        """
        Detect faces in an image and generate face embeddings.
        
        This method performs the complete face detection and recognition pipeline:
        1. Loads the image using OpenCV
        2. Uses YOLO to detect face bounding boxes
        3. Extracts face regions with padding
        4. Generates face embeddings using FaceNet
        5. Stores face data in the database
        
        Args:
            image_id (int): Unique identifier for the image
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary containing detection results with:
                - ids: Class IDs from YOLO detection
                - processed_faces: Preprocessed face images
                - num_faces: Number of faces detected
            None: If image loading fails
        """
        # Load image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return None

        # Detect faces using YOLO model
        boxes, scores, class_ids = self.yolo_detector(img)
        print(boxes)
        print(f"Detected {len(boxes)} faces in image {image_id}.")

        # Initialize lists for storing face data
        processed_faces, embeddings, bboxes, confidences = [], [], [], []

        # Process each detected face
        for box, score in zip(boxes, scores):
            # Only process faces above confidence threshold
            if score > self.yolo_detector.conf_threshold:
                # Extract bounding box coordinates
                x1, y1, x2, y2 = map(int, box)

                # Create bounding box dictionary in JSON format for database storage
                bbox = {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}
                bboxes.append(bbox)
                confidences.append(float(score))

                # Extract face region with padding for better recognition
                padding = 20
                face_img = img[
                    max(0, y1 - padding) : min(img.shape[0], y2 + padding),
                    max(0, x1 - padding) : min(img.shape[1], x2 + padding),
                ]
                
                # Preprocess face image for FaceNet
                processed_face = FaceNet_util_preprocess_image(face_img)
                processed_faces.append(processed_face)

                # Generate face embedding using FaceNet
                embedding = self.facenet.get_embedding(processed_face)
                embeddings.append(embedding)

        # Store face embeddings in database if any faces were detected
        if embeddings:
            db_insert_face_embeddings_by_image_id(
                image_id, embeddings, confidence=confidences, bbox=bboxes
            )

        # Return detection results
        return {
            "ids": f"{class_ids}",
            "processed_faces": processed_faces,
            "num_faces": len(embeddings),
        }

    def close(self):
        """
        Close the resources held by the FaceDetector.
        
        Properly releases memory and resources used by the YOLO detector
        and FaceNet model to prevent memory leaks.
        """
        # Close YOLO detector and release resources
        if self.yolo_detector is not None:
            self.yolo_detector.close()
            self.yolo_detector = None

        # Close FaceNet model and release resources
        if self.facenet is not None:
            self.facenet.close()
            self.facenet = None
