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
        session = onnxruntime.InferenceSession(
            model_path, providers=onnxruntime.get_available_providers()
        )
        yield session
    except Exception as e:
        logger.error(f"Error in ONNX session: {str(e)}")
        raise
    finally:
        if session:
            del session


# This context manager function creates and yields an ONNX runtime InferenceSession for the given model path.
# It ensures that the session is properly initialized with available providers and that resources are cleaned up afterwards.
# If an error occurs during session creation or usage, it logs the error and re-raises the exception.
# Using this context manager helps manage the ONNX session lifecycle safely and cleanly within a `with` statement.
