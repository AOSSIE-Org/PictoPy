from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import os
from app.models.Inpainter import Inpainter
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize Inpainter - GLOBAL instance to avoid reloading model
inpainter = Inpainter()

class MagicEraserRequest(BaseModel):
    image_path: str
    mask_data: str # Base64 string

class MagicEraserResponse(BaseModel):
    success: bool
    image_data: str | None = None # Base64 string
    error: str | None = None

def base64_to_cv2(b64str):
    if "," in b64str:
        b64str = b64str.split(",")[1]
    img_data = base64.b64decode(b64str)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    return img

def cv2_to_base64(img):
    _, buffer = cv2.imencode('.png', img)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"

@router.post("/magic-eraser", response_model=MagicEraserResponse)
def magic_eraser(body: MagicEraserRequest):
    try:
        # Custom Validation: Prevent Path Traversal
        # Ensure path is absolute and doesn't contain traversal sequences
        abs_path = os.path.abspath(body.image_path)
        base_dir = os.path.abspath(os.getcwd()) # Or a specific allowed media directory
        
        # Simple check for ".." usage which suggests traversal attempts
        if ".." in body.image_path:
             return MagicEraserResponse(success=False, error="Invalid image path: Path traversal detected")

        if not os.path.exists(abs_path):
             return MagicEraserResponse(success=False, error="Image file not found")
        
        image = cv2.imread(body.image_path)
        if image is None:
             return MagicEraserResponse(success=False, error="Failed to load image file")

        # 2. Load Mask
        mask = base64_to_cv2(body.mask_data)
        if mask is None:
            return MagicEraserResponse(success=False, error="Failed to decode mask data")
        
        # Ensure mask is single channel
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            
        # 3. Inpaint
        result = inpainter.inpaint(image, mask)
        
        # 4. Return result as Base64 for preview
        b64_result = cv2_to_base64(result)
        
        return MagicEraserResponse(success=True, image_data=b64_result)

    except Exception as e:
        logger.exception("Magic Eraser failed")
        return MagicEraserResponse(success=False, error="Internal processing error")
