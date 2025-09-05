"""
Sync Microservice Lifespan Management

This module manages the application lifecycle for the PictoPy sync microservice.
It handles startup and shutdown events, including database connection verification
and file system watcher initialization/cleanup.

Key Responsibilities:
- Database connection validation on startup
- File system watcher initialization
- Graceful shutdown handling
- Resource cleanup on application termination
"""

# Standard library imports
from contextlib import asynccontextmanager

# Third-party imports
from fastapi import FastAPI

# Application imports
from app.database.folders import db_check_database_connection
from app.utils.watcher import (
    watcher_util_start_folder_watcher,
    watcher_util_stop_folder_watcher,
)

# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================

# Global variable to track file system watcher status
# Used to ensure proper cleanup during shutdown
watcher_started = False


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifespan - startup and shutdown events.
    
    This function handles the complete lifecycle of the sync microservice:
    
    Startup Phase:
    - Initialize database connection
    - Start file system watcher
    - Verify all services are operational
    
    Shutdown Phase:
    - Stop file system watcher
    - Clean up resources
    - Log shutdown completion
    
    Args:
        app: FastAPI application instance
        
    Raises:
        RuntimeError: If database connection fails during startup
    """
    global watcher_started

    try:
        # =====================================================================
        # STARTUP PHASE
        # =====================================================================
        print("Starting PictoPy Sync Microservice...")

        # Verify database connection to main PictoPy backend
        if not db_check_database_connection():
            print("Failed to connect to PictoPy database")
            print(
                "Make sure the main PictoPy backend is set up and the database exists"
            )
            raise RuntimeError("Database connection failed")

        print("Database connection successful")

        # Initialize file system watcher for folder monitoring
        watcher_started = watcher_util_start_folder_watcher()

        print("Sync microservice is ready!")

        # Application is ready to serve requests
        yield

    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print("\nReceived keyboard interrupt (Ctrl+C)")
        print("Initiating graceful shutdown...")
    except Exception as e:
        # Handle unexpected errors during startup
        print(f"Unexpected error during startup: {e}")
        raise
    finally:
        # =====================================================================
        # SHUTDOWN PHASE
        # =====================================================================
        print("Shutting down sync microservice...")
        
        # Stop file system watcher if it was started
        if watcher_started:
            watcher_util_stop_folder_watcher()
            print("Folder watcher stopped")
            
        print("Shutdown complete")
