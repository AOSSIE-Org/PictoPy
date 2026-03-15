import onnxruntime
import logging
from typing import Optional


def ONNX_util_get_execution_providers() -> list:
    """
    Get ONNX execution providers based on GPU acceleration setting from metadata.

    Returns:
        list: List of execution providers for ONNX runtime
              - If GPU_Acceleration is False: ["CPUExecutionProvider"]
              - If GPU_Acceleration is True: All available providers
    """
    from app.database.metadata import db_get_metadata

    # Get metadata from database
    metadata = db_get_metadata()

    # Default to CPU if no preferences found
    gpu_acceleration = True

    # Extract GPU acceleration setting from user preferences
    if metadata and "user_preferences" in metadata:
        user_prefs = metadata["user_preferences"]
        gpu_acceleration = user_prefs.get("GPU_Acceleration", True)

    # Return appropriate execution providers
    if gpu_acceleration:
        return onnxruntime.get_available_providers()
    else:
        return ["CPUExecutionProvider"]


def create_inference_session_with_fallback(
    model_path: str,
    logger: logging.Logger,
    model_name: str = ""
) -> onnxruntime.InferenceSession:
    """
    Create an ONNX InferenceSession with fallback to CPUExecutionProvider on failure.

    Args:
        model_path (str): Path to the ONNX model file.
        logger (logging.Logger): Logger instance.
        model_name (str): Optional name of the model for logging purposes.

    Returns:
        onnxruntime.InferenceSession: The initialized inference session.

    Raises:
        Exception: If initialization fails even with the fallback.
    """
    try:
        return onnxruntime.InferenceSession(
            model_path, providers=ONNX_util_get_execution_providers()
        )
    except Exception as e:
        logger.warning(
            f"Failed to initialize InferenceSession with default providers: {e}. Falling back to CPUExecutionProvider."
        )
        try:
            return onnxruntime.InferenceSession(
                model_path, providers=["CPUExecutionProvider"]
            )
        except Exception as cpu_e:
            model_str = f"{model_name} " if model_name else ""
            logger.error(
                f"Failed to initialize {model_str}InferenceSession with CPUExecutionProvider: {cpu_e}"
            )
            raise
