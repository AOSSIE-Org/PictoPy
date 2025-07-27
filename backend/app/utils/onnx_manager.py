import onnxruntime
from contextlib import contextmanager
import gc
import logging
from typing import Dict
import weakref

logger = logging.getLogger(__name__)

# Session pool to reuse sessions
_session_pool: Dict[str, weakref.ref] = {}

def _create_session(model_path: str) -> onnxruntime.InferenceSession:
    """Create an optimized ONNX session."""
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if "CUDAExecutionProvider" in onnxruntime.get_available_providers()
        else ["CPUExecutionProvider"]
    )
    
    # Optimize session settings
    sess_options = onnxruntime.SessionOptions()
    sess_options.enable_mem_pattern = True
    sess_options.enable_cpu_mem_arena = True
    sess_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = 1
    sess_options.inter_op_num_threads = 1
    sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
    
    return onnxruntime.InferenceSession(
        model_path,
        providers=providers,
        sess_options=sess_options
    )

def _cleanup_session(session):
    """Clean up session resources."""
    try:
        # Force release of ONNX runtime resources
        session._sess = None
        del session
    except:
        pass
    finally:
        # Force garbage collection
        gc.collect()

@contextmanager
def onnx_session(model_path: str):
    """Context manager for ONNX runtime sessions with memory optimization."""
    session = None
    try:
        # Try to get existing session from pool
        session_ref = _session_pool.get(model_path)
        if session_ref is not None:
            session = session_ref()
        
        # Create new session if none exists or reference is dead
        if session is None:
            session = _create_session(model_path)
            _session_pool[model_path] = weakref.ref(session)
        
        yield session
    
    finally:
        if session is not None and model_path not in _session_pool:
            _cleanup_session(session)
