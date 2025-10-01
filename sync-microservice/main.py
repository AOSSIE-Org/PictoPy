import sys
from fastapi import FastAPI
from uvicorn import Config, Server
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware
from app.logging.setup_logging import get_sync_logger, configure_uvicorn_logging, setup_logging

# Set up standard logging
setup_logging("sync-microservice")

# Configure Uvicorn logging to use our custom formatter
configure_uvicorn_logging("sync-microservice")

# Use the sync-specific logger for this module
logger = get_sync_logger(__name__)


class LoggerWriter:
    """Custom writer that redirects stdout/stderr to logger."""

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message):
        # Buffer the message until we get a complete line
        self.buffer += message
        if message.endswith("\n"):
            # Log the complete line (minus the newline)
            line = self.buffer.rstrip("\n")
            if line:  # Only log non-empty lines
                self.logger.log(self.level, line)
            self.buffer = ""

    def flush(self):
        # Flush any remaining buffer content
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ""


# Redirect stdout and stderr to logger
sys.stdout = LoggerWriter(logger, 20)  # INFO level
sys.stderr = LoggerWriter(logger, 40)  # ERROR level

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
app.include_router(health.router, prefix="/api/v1")
app.include_router(watcher.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")

if __name__ == "__main__":
    # Get a logger for this module
    logger = get_sync_logger(__name__)
    logger.info("Starting PictoPy Sync Microservice...")

    # Create config with log_config=None to disable Uvicorn's default logging
    config = Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        log_config=None,  # Disable uvicorn's default logging config
    )
    server = Server(config)
    server.run()
