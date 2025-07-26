from contextlib import contextmanager
import logging
import onnxruntime

logger = logging.getLogger(__name__)


@contextmanager
def onnx_session(model_path: str):
    """
    Context manager for ONNX runtime sessions to ensure proper resource management.

    Args:
        model_path (str): Path to the ONNX model file

    Yields:
        onnxruntime.InferenceSession: The ONNX runtime session
    """
    session = None
    try:
        # Create an ONNX runtime inference session using available providers
        session = onnxruntime.InferenceSession(
            model_path, providers=onnxruntime.get_available_providers()
        )
        yield session  # Provide the session to the context block
    except Exception as e:
        # Log any error encountered during session creation or use
        logger.error(f"Error in ONNX session: {str(e)}")
        raise
    finally:
        # Ensure session is properly deleted/freed after use
        if session:
            del session
