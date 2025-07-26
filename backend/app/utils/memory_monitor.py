import psutil
import logging
from functools import wraps
from typing import Callable
import time

logger = logging.getLogger(__name__)


def log_memory_usage(func: Callable) -> Callable:
    """
    Decorator to log memory usage before and after function execution.

    Args:
        func: The function to monitor

    Returns:
        Wrapped function with memory monitoring
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()

        # Memory before execution
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()

        # Execute function
        result = func(*args, **kwargs)

        # Memory after execution
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        end_time = time.time()

        # Log memory usage
        logger.info(
            f"Memory usage for {func.__name__}:\n"
            f"  Before: {mem_before:.2f}MB\n"
            f"  After: {mem_after:.2f}MB\n"
            f"  Difference: {mem_after - mem_before:.2f}MB\n"
            f"  Execution time: {(end_time - start_time)*1000:.2f}ms"
        )

        return result

    return wrapper


# This decorator function wraps any function passed to it and logs the memory usage (in MB)
# before and after the function's execution, along with the difference and the execution time.
# It helps to monitor the memory impact of specific function calls during runtime.

def get_current_memory_usage() -> float:
    """Returns current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


# This function returns the current memory usage of the running process in megabytes (MB).
# It can be called anytime to check how much memory the process is consuming at that moment.
