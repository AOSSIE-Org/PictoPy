"""
Test module for the centralized logging system.

This module demonstrates how to use the logging system and validates
that the setup works correctly for both components.
"""

import os
import sys
from pathlib import Path

# Add necessary paths to sys.path to enable imports
backend_path = Path(__file__).parent.parent / "backend"
sync_path = Path(__file__).parent.parent / "sync-microservice"

sys.path.append(str(backend_path))
sys.path.append(str(sync_path))

# First initialize the logging system by importing the setup modules
from utils.logging.core import setup_logging, get_logger

# Then import the component-specific loggers
try:
    from backend.app.logging import get_backend_logger
    HAS_BACKEND = True
except ImportError:
    HAS_BACKEND = False
    print("WARNING: Backend logging module not found. Skipping backend tests.")

try:
    from sync_microservice.app.logging import get_sync_logger
    HAS_SYNC = True
except ImportError:
    HAS_SYNC = False
    print("WARNING: Sync-microservice logging module not found. Skipping sync tests.")


def test_backend_logging():
    """Test logging from the backend component."""
    if not HAS_BACKEND:
        print("Skipping backend logging test.")
        return
        
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
    if not HAS_SYNC:
        print("Skipping sync-microservice logging test.")
        return
        
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
    # Store original environment setting
    original_env = os.environ.get("ENV")
    
    # Test production environment (should only show INFO and above)
    os.environ["ENV"] = "production"
    
    # We need to reload the logging setup
    setup_logging("backend")
    
    if HAS_BACKEND:
        logger = get_backend_logger(__name__)
        print("\n=== Testing Production Environment Settings ===")
        logger.debug("This DEBUG message should NOT appear in production")
        logger.info("This INFO message should appear in production")
    
    # Reset to development environment
    if original_env:
        os.environ["ENV"] = original_env
    else:
        os.environ.pop("ENV", None)
    
    # Reload for development environment
    setup_logging("backend")
    
    if HAS_BACKEND:
        print("\n=== Testing Development Environment Settings ===")
        logger.debug("This DEBUG message should appear in development")


if __name__ == "__main__":
    # Run all tests
    test_backend_logging()
    test_sync_microservice_logging()
    test_environment_settings()
    
    print("\nLogging test completed.")