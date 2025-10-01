"""
Test module for the Loguru-based logging system.

This module demonstrates how to use the logging system and validates
that the setup works correctly for both components.
"""

import os
import sys
from pathlib import Path
import importlib

# Add components directories to path to enable imports
backend_path = Path(__file__).parent.parent / "backend"
sync_path = Path(__file__).parent.parent / "sync-microservice"

sys.path.append(str(backend_path))
sys.path.append(str(sync_path))

# Import the loggers after adding paths
# These imports are placed here intentionally after modifying sys.path
from backend.app.logging import get_backend_logger  # noqa: E402
from sync_microservice.app.logging import get_sync_logger  # noqa: E402


def test_backend_logging():
    """Test logging from the backend component."""
    # Get a logger with the module name
    logger = get_backend_logger(__name__)

    print("\n=== Testing Backend Logging ===")
    logger.debug("This is a DEBUG message from backend")
    logger.info("This is an INFO message from backend")
    logger.warning("This is a WARNING message from backend")
    logger.error("This is an ERROR message from backend")
    logger.critical("This is a CRITICAL message from backend")


def test_sync_microservice_logging():
    """Test logging from the sync-microservice component."""
    # Get a logger with the module name
    logger = get_sync_logger(__name__)

    print("\n=== Testing Sync-Microservice Logging ===")
    logger.debug("This is a DEBUG message from sync-microservice")
    logger.info("This is an INFO message from sync-microservice")
    logger.warning("This is a WARNING message from sync-microservice")
    logger.error("This is an ERROR message from sync-microservice")
    logger.critical("This is a CRITICAL message from sync-microservice")


def test_environment_settings():
    """Test logging with different environment settings."""
    import importlib

    # First store current environment setting
    original_env = os.environ.get("ENV")

    # Test production mode (should only show INFO and above)
    os.environ["ENV"] = "production"

    # Need to reimport the modules to apply new environment setting
    # This will force reloading the setup_logging modules
    from backend.app.logging import setup_logging as backend_setup

    importlib.reload(backend_setup)

    logger = get_backend_logger(__name__)

    print("\n=== Testing Production Environment Settings ===")
    logger.debug("This DEBUG message should NOT appear in production")
    logger.info("This INFO message should appear in production")

    # Reset to development mode
    if original_env:
        os.environ["ENV"] = original_env
    else:
        os.environ.pop("ENV", None)

    # Reload again for development mode
    importlib.reload(backend_setup)

    print("\n=== Testing Development Environment Settings ===")
    logger.debug("This DEBUG message should appear in development")


if __name__ == "__main__":
    # Run all tests
    test_backend_logging()
    test_sync_microservice_logging()
    test_environment_settings()

    print("\nAll logging tests completed.")
