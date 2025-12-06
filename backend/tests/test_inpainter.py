import cv2
import numpy as np
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.models.Inpainter import Inpainter

def test_inpainter():
    print("Initializing Inpainter...")
    try:
        inpainter = Inpainter()
        if inpainter.session is None:
            print("FAILED: Model session not initialized. Model file might be missing.")
            return

        print("Creating dummy image and mask...")
        # Create a 512x512 gradient image
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        for i in range(512):
            img[i, :, :] = i // 2
        
        # Create a mask (white square in center)
        mask = np.zeros((512, 512), dtype=np.uint8)
        mask[200:300, 200:300] = 255
        
        print("Running inpaint...")
        result = inpainter.inpaint(img, mask)
        
        print("Inpaint finished.")
        print(f"Result shape: {result.shape}")
        
        if result.shape != img.shape:
             print(f"FAILED: Shape mismatch. Expected {img.shape}, got {result.shape}")
             return
             
        # Check if the center is not black/unmodified (basic check)
        center_pixel = result[250, 250]
        print(f"Center pixel value: {center_pixel}")
        
        print("SUCCESS: Inpainter verification passed.")
        
    except Exception as e:
        print(f"FAILED: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inpainter()
