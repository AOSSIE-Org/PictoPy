import cv2
import numpy as np
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def siglip_util_preprocess_image(img_path: str, resolution: int) -> np.ndarray | None:
    """
    Preprocess image for SigLIP vision model.
    Loads, resizes, normalizes, and transposes the image.
    Returns a [3, R, R] float32 array or None if the image is corrupt/unreadable.
    """
    img = cv2.imread(img_path)
    if img is None:
        logger.error(f"Failed to load image for SigLIP preprocessing: {img_path}")
        return None

    # cv2 loads BGR; SigLIP expects RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Matches HF SiglipImageProcessor's bicubic default
    img = cv2.resize(img, (resolution, resolution), interpolation=cv2.INTER_CUBIC)

    img = img.astype(np.float32) * (1 / 255.0)

    # Normalize: (x - 0.5) / 0.5 (SigLIP mean=std=0.5 per channel)
    img = (img - 0.5) / 0.5

    # Transpose HWC -> CHW
    img = np.transpose(img, (2, 0, 1))

    return img


_tokenizer = None
_tokenizer_key = None


def siglip_util_tokenize_query(query: str) -> tuple[np.ndarray, np.ndarray]:
    global _tokenizer, _tokenizer_key
    from app.config.settings import (
        SIGLIP2_ACTIVE_CHECKPOINT,
        SIGLIP2_TEXT_MAX_LENGTH,
        SIGLIP2_TOKENIZER_PAD_ID,
        SIGLIP2_TOKENIZER_PAD_TOKEN,
    )
    from app.models.model_registry import get_siglip2_tokenizer_key, get_model_path
    from tokenizers import Tokenizer
    import numpy as np

    current_key = get_siglip2_tokenizer_key(SIGLIP2_ACTIVE_CHECKPOINT)

    if _tokenizer is None or _tokenizer_key != current_key:
        tokenizer_path = get_model_path(current_key)
        _tokenizer = Tokenizer.from_file(tokenizer_path)
        _tokenizer.enable_truncation(max_length=SIGLIP2_TEXT_MAX_LENGTH)
        _tokenizer.enable_padding(
            length=SIGLIP2_TEXT_MAX_LENGTH,
            pad_id=SIGLIP2_TOKENIZER_PAD_ID,
            pad_token=SIGLIP2_TOKENIZER_PAD_TOKEN,
        )
        _tokenizer_key = current_key

    encoding = _tokenizer.encode(query)
    input_ids = np.array(encoding.ids, dtype=np.int64).reshape(
        1, SIGLIP2_TEXT_MAX_LENGTH
    )

    # attention_mask: np.ones, NOT encoding's mask.
    # SigLIP trains fixed-length without pad masking; ONNX export validated with all-ones mask.
    # Encoding's real mask (zeros on padding) would deviate from validated numbers.
    attention_mask = np.ones((1, SIGLIP2_TEXT_MAX_LENGTH), dtype=np.int64)

    return input_ids, attention_mask
