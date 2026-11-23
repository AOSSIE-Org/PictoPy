import onnxruntime


def ONNX_util_get_execution_providers(exclude: tuple[str, ...] = ()) -> list:
    """
    Get ONNX execution providers based on GPU acceleration setting from metadata.

    Args:
        exclude: Provider names to filter out (e.g. providers known to be
                 incompatible with a specific model graph).

    Returns:
        list: List of execution providers for ONNX runtime
              - If GPU_Acceleration is False: ["CPUExecutionProvider"]
              - If GPU_Acceleration is True: All available providers minus `exclude`
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
        providers = [
            p for p in onnxruntime.get_available_providers() if p not in exclude
        ]
        return providers or ["CPUExecutionProvider"]
    else:
        return ["CPUExecutionProvider"]


def ONNX_util_get_session_options(
    intra_op_num_threads: int | None = None,
) -> onnxruntime.SessionOptions:
    """
    Get configured ONNX SessionOptions to prevent CPU thread oversubscription.

    Args:
        intra_op_num_threads: Number of threads for intra-operator parallelism.
                              Defaults to ONNX_INTRA_OP_NUM_THREADS setting (default 1).

    Returns:
        onnxruntime.SessionOptions configured with sequential execution mode
        and thread limits.
    """
    if intra_op_num_threads is not None and intra_op_num_threads < 1:
        raise ValueError(
            f"intra_op_num_threads must be >= 1, got {intra_op_num_threads}"
        )

    from app.config.settings import ONNX_INTRA_OP_NUM_THREADS

    sess_options = onnxruntime.SessionOptions()
    sess_options.intra_op_num_threads = (
        intra_op_num_threads
        if intra_op_num_threads is not None
        else ONNX_INTRA_OP_NUM_THREADS
    )
    sess_options.inter_op_num_threads = 1
    sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
    return sess_options
