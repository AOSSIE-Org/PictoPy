
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to find backend modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Mock heavy dependencies and models to isolate unit tests
sys.modules['app.models.FaceNet'] = MagicMock()
sys.modules['app.utils.FaceNet'] = MagicMock()
sys.modules['app.utils.YOLO'] = MagicMock()
sys.modules['app.models.YOLO'] = MagicMock()
sys.modules['app.database.faces'] = MagicMock()
sys.modules['app.logging.setup_logging'] = MagicMock()

try:
    from app.models.FaceDetector import FaceDetector
    import cv2
    from fastapi import HTTPException
except ImportError:
    FaceDetector = None

class TestFaceDetector(unittest.TestCase):
    def setUp(self):
        if FaceDetector is None:
            self.skipTest("FaceDetector or dependencies could not be imported")

    @patch('cv2.imread')
    def test_detect_faces_invalid_image_raises_400(self, mock_imread):
        """
        Ensure detect_faces raises HTTPException(400) when image reading fails.
        """
        # Simulate cv2.imread failing (returning None)
        mock_imread.return_value = None
        
        detector = FaceDetector()
        
        with self.assertRaises(HTTPException) as context:
            detector.detect_faces("test_id", "invalid/path/image.jpg")
            
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid or unreadable image file")

    @patch('cv2.imread')
    def test_detect_faces_valid_image(self, mock_imread):
        """
        Ensure detect_faces processes valid images correctly without error.
        """
        # Simulate valid image load
        mock_img = MagicMock()
        mock_imread.return_value = mock_img
        
        detector = FaceDetector()
        # Mock detection results: boxes, scores, class_ids
        detector.yolo_detector.return_value = ([], [], [])
        
        result = detector.detect_faces("test_id", "valid.jpg")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["num_faces"], 0)

if __name__ == '__main__':
    unittest.main()
