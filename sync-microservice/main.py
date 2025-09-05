"""
PictoPy Sync Microservice Main Application

This module contains the main FastAPI application for the PictoPy sync microservice.
The sync microservice handles file system monitoring, folder synchronization,
and background processing tasks for the main PictoPy application.

Key Features:
- File system monitoring and change detection
- Folder synchronization and indexing
- Health check endpoints for service monitoring
- Background processing for image analysis tasks
- Integration with the main PictoPy backend

The microservice runs on port 8001 and provides RESTful APIs for:
- Health monitoring and service status
- File system watching and change notifications
- Folder management and synchronization
"""

# Standard library imports
from fastapi import FastAPI
from uvicorn import Config, Server

# Application imports
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders

# =============================================================================
# FASTAPI APPLICATION CONFIGURATION
# =============================================================================

# Create FastAPI application with lifespan management
app = FastAPI(
    title="PictoPy Sync Microservice",
    description="File system synchronization service for PictoPy",
    version="1.0.0",
    lifespan=lifespan,  # Custom lifespan manager for startup/shutdown events
)

# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

# Register API route modules with versioned prefixes
app.include_router(health.router, prefix="/api/v1")    # Health check endpoints
app.include_router(watcher.router, prefix="/api/v1")   # File system watching
app.include_router(folders.router, prefix="/api/v1")   # Folder management

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Configure uvicorn server for direct execution
    config = Config(app=app, host="0.0.0.0", port=8001, log_config=None)
    server = Server(config)
    
    # Start the sync microservice
    server.run()
