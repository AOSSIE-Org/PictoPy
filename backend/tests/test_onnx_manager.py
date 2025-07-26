import pytest
import os
import numpy as np
from app.utils.onnx_manager import onnx_session
from app.utils.memory_monitor import get_current_memory_usage


def test_onnx_session_context_manager():
    # Test model path
    model_path = "app/models/yolov8n.onnx"

    if not os.path.exists(model_path):
        pytest.skip(f"Model file not found: {model_path}")

    initial_memory = get_current_memory_usage()

    # Test multiple session creations
    for _ in range(5):
        with onnx_session(model_path) as session:
            assert session is not None
            # Perform a dummy inference to ensure session works
            input_name = session.get_inputs()[0].name
            input_shape = session.get_inputs()[0].shape
            dummy_input = np.zeros(input_shape, dtype=np.float32)
            session.run(None, {input_name: dummy_input})

    # Check memory after sessions
    final_memory = get_current_memory_usage()
    memory_diff = final_memory - initial_memory

    # Allow for some memory overhead, but it shouldn't be excessive
    assert memory_diff < 100, f"Memory leak detected: {memory_diff:.2f}MB increase"
# Tests the ONNX session context manager by creating multiple sessions, running dummy inferences,
# and verifying no significant memory leaks occur during repeated session usage.
