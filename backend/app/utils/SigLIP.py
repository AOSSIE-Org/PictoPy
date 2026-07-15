import threading
import numpy as np
from PIL import Image
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def siglip_util_preprocess_image(img_path: str, resolution: int) -> np.ndarray | None:
    """
    Preprocess image for SigLIP vision model.
    Loads, resizes, normalizes, and transposes the image.
    Returns a [3, R, R] float32 array or None if the image is corrupt/unreadable.
    """
    try:
        # PIL bicubic (antialiased, Pillow>=9.1). Measured vs HF
        # SiglipImageProcessor on real 4032x3024 photos: embedding cosine
        # ~0.984 (HF uses an internal resampler that plain PIL resize does
        # not reproduce; exact parity would require shipping transformers).
        # Production is self-consistent: SIGLIP2_MATCH_THRESHOLD was tuned
        # against THIS pipeline. Any future threshold/calibration work must
        # use this function, not AutoImageProcessor.
        img = (
            Image.open(img_path)
            .convert("RGB")
            .resize((resolution, resolution), Image.BICUBIC)
        )

        # Convert to numpy array and normalize to [0, 1]
        img_np = np.asarray(img).astype(np.float32) / 255.0

        # Normalize: (x - 0.5) / 0.5 (SigLIP mean=std=0.5 per channel)
        img_np = (img_np - 0.5) / 0.5

        # Transpose HWC -> CHW
        img_np = np.transpose(img_np, (2, 0, 1))

        return img_np
    except Exception as e:
        logger.error(f"Failed to load/preprocess image for SigLIP: {img_path} - {e}")
        return None


_tokenizer = None
_tokenizer_key = None
_tokenizer_lock = threading.Lock()


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

    # Lock around the check-load-assign sequence only: without it, two
    # threads racing on a cold/stale cache could both load a tokenizer and
    # interleave their _tokenizer/_tokenizer_key assignments, leaving the
    # pair mismatched. encode() itself doesn't touch the cache, so it runs
    # outside the lock on a captured local -- no need to serialize it.
    with _tokenizer_lock:
        if _tokenizer is None or _tokenizer_key != current_key:
            tokenizer_path = get_model_path(current_key)
            tokenizer = Tokenizer.from_file(tokenizer_path)
            tokenizer.enable_truncation(max_length=SIGLIP2_TEXT_MAX_LENGTH)
            tokenizer.enable_padding(
                length=SIGLIP2_TEXT_MAX_LENGTH,
                pad_id=SIGLIP2_TOKENIZER_PAD_ID,
                pad_token=SIGLIP2_TOKENIZER_PAD_TOKEN,
            )
            _tokenizer = tokenizer
            _tokenizer_key = current_key

        tokenizer = _tokenizer

    encoding = tokenizer.encode(query)
    input_ids = np.array(encoding.ids, dtype=np.int64).reshape(
        1, SIGLIP2_TEXT_MAX_LENGTH
    )

    # attention_mask: np.ones, NOT encoding's mask.
    # SigLIP trains fixed-length without pad masking; ONNX export validated with all-ones mask.
    # Encoding's real mask (zeros on padding) would deviate from validated numbers.
    attention_mask = np.ones((1, SIGLIP2_TEXT_MAX_LENGTH), dtype=np.int64)

    return input_ids, attention_mask


_text_model = None
_text_model_key = None
_text_model_lock = threading.Lock()


def siglip_util_get_text_model(model_path: str, model_key: str):
    """Lazily create and cache a SigLIP2Text session across requests.
    The text tower is ~1GB; reloading + closing it on every
    /semantic-search call was the dominant per-request cost. The cache is
    swapped (old session closed) when the active checkpoint changes, and
    can be dropped early via siglip_util_invalidate_text_model."""
    global _text_model, _text_model_key
    from app.models.SigLIP2Text import SigLIP2Text

    with _text_model_lock:
        if _text_model is None or _text_model_key != model_key:
            if _text_model is not None:
                _text_model.close()
            _text_model = SigLIP2Text(model_path)
            _text_model_key = model_key
        return _text_model


def siglip_util_invalidate_text_model(model_key: str | None = None) -> None:
    """Close and drop the cached text model session.

    Must be called before uninstalling a SigLIP2 text model: the cache
    holds a session registered with session_registry, so its active-session
    count would never reach zero (blocking the uninstall guard forever)
    unless this closes it first. If model_key is given, only invalidates
    when it matches the currently cached model.
    """
    global _text_model, _text_model_key
    with _text_model_lock:
        if _text_model is not None and (
            model_key is None or _text_model_key == model_key
        ):
            _text_model.close()
            _text_model = None
            _text_model_key = None
