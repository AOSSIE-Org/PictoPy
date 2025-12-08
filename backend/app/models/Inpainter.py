
import cv2
import numpy as np
import onnxruntime as ort
import os
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

class Inpainter:
    def __init__(self):
        self.output_img_size = 512 # LaMa fixed input size
        self._init_session()

    def _init_session(self):
        """Initialize the ONNX Runtime session."""
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models",
            "onnx_models",
            "lama_fp32.onnx"
        )
        
        if not os.path.exists(model_path):
            logger.error(f"Inpainting model not found at {model_path}")
            self.session = None
            return

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
             providers = ['CPUExecutionProvider']
        
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
            logger.info(f"Inpainting model loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load inpainting model: {e}")
            self.session = None

    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Perform inpainting on the image using the mask.
        :param image: Input image (H, W, 3) BGR
        :param mask: Input mask (H, W) or (H, W, 1) 0-255 (255=inpainting area)
        :return: Inpainted image (H, W, 3) BGR
        """
        if self.session is None:
             # Try to re-init if it failed previously (e.g. download finished)
             self._init_session()
             if self.session is None:
                 raise RuntimeError("Inpainting model not loaded.")

        original_h, original_w = image.shape[:2]

        # 1. Preprocess
        # Resize/Pad to 512x512
        # For simplicity, we'll just resize to 512x512. 
        # LaMa is resilient, but aspect ratio distortion might affect quality slightly.
        # Ideally, we should pad, but resizing is faster/easier for V1.
        # Let's try resizing first.
        
        img_resized = cv2.resize(image, (self.output_img_size, self.output_img_size), interpolation=cv2.INTER_AREA)
        mask_resized = cv2.resize(mask, (self.output_img_size, self.output_img_size), interpolation=cv2.INTER_NEAREST)

        # Normalize Image: [0, 255] -> [0, 1], HWC -> CHW
        img_input = img_resized.astype(np.float32) / 255.0
        img_input = np.transpose(img_input, (2, 0, 1)) # (3, 512, 512)
        img_input = np.expand_dims(img_input, axis=0) # (1, 3, 512, 512)

        # Normalize Mask: [0, 255] -> [0, 1], HW -> CHW
        if len(mask_resized.shape) == 2:
            mask_resized = np.expand_dims(mask_resized, axis=-1) # (512, 512, 1)
        
        mask_input = mask_resized.astype(np.float32) / 255.0
        mask_input = (mask_input > 0.5).astype(np.float32) # threshold
        mask_input = np.transpose(mask_input, (2, 0, 1)) # (1, 512, 512)
        mask_input = np.expand_dims(mask_input, axis=0) # (1, 1, 512, 512)

        # 2. Inference
        inputs = {
            self.session.get_inputs()[0].name: img_input,
            self.session.get_inputs()[1].name: mask_input
        }
        outputs = self.session.run(None, inputs)
        output_data = outputs[0] # (1, 3, 512, 512)

        # 3. Postprocess
        # Clip to [0, 255], CHW -> HWC
        output_img = output_data[0]
        output_img = np.transpose(output_img, (1, 2, 0)) # (512, 512, 3)
        
        # Auto-detect output range: LaMa can be [0, 1] or [0, 255]
        # If max value is small (<= 1.0 + epsilon), assume it's [0, 1] and scale up.
        if output_img.max() <= 1.1:
            output_img = output_img * 255.0
            
        output_img = np.clip(output_img, 0, 255).astype(np.uint8)

        # Resize back to original
        result_img = cv2.resize(output_img, (original_w, original_h), interpolation=cv2.INTER_CUBIC)
        
        # 4. Blend to preserve original quality
        # Create a binary mask of the inpainted region
        if len(mask.shape) == 2:
            mask = mask[:, :, np.newaxis]
        
        # Normalize mask to 0-1
        mask_normalized = mask.astype(np.float32) / 255.0
        mask_normalized = (mask_normalized > 0.5).astype(np.float32)
        
        # Blend: original * (1 - mask) + result * mask
        final_img = image.astype(np.float32) * (1 - mask_normalized) + result_img.astype(np.float32) * mask_normalized
        final_img = np.clip(final_img, 0, 255).astype(np.uint8)
        
        return final_img
