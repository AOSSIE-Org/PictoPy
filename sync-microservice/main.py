import logging
from fastapi import FastAPI
from uvicorn import Config, Server
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware
from app.logging.setup_logging import (
    get_sync_logger,
    configure_uvicorn_logging,
    setup_logging,
)
from app.utils.logger_writer import redirect_stdout_stderr

# Set up standard logging
setup_logging("sync-microservice")

# Configure Uvicorn logging to use our custom formatter
configure_uvicorn_logging("sync-microservice")

# Use the sync-specific logger for this module
logger = get_sync_logger(__name__)

logger.info("Starting PictoPy Sync Microservice...")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="PictoPy Sync Microservice",
    description="File system synchronization service for PictoPy",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include route modules
app.include_router(health.router, tags=["Health"])
app.include_router(watcher.router, prefix="/watcher", tags=["Watcher"])
app.include_router(folders.router, prefix="/folders", tags=["Folders"])

if __name__ == "__main__":
    logger.info("Starting PictoPy Sync Microservice")

    # Create config with log_config=None to disable Uvicorn's default logging
    config = Config(
        app=app,
        host="localhost",
        port=52124,
        log_level="info",
        log_config=None,  # Disable uvicorn's default logging config
    )
    server = Server(config)

    # Use context manager for safe stdout/stderr redirection
    with redirect_stdout_stderr(
        logger, stdout_level=logging.INFO, stderr_level=logging.ERROR
    ):
        server.run()
