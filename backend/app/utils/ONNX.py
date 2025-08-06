import onnxruntime


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
