import logging

from fastapi import FastAPI
from uvicorn import Config, Server

from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware
from app.logging.setup_logging import get_sync_logger, configure_uvicorn_logging, setup_logging
from app.utils.logger_writer import redirect_stdout_stderr

# Set up standard logging
setup_logging()

# Configure Uvicorn logging
configure_uvicorn_logging()

# Get logger
logger = get_sync_logger(__name__)

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Define allowed origins
origins = [
    "http://localhost:1420",
    "http://localhost:5173",
    "tauri://localhost",
    "https://tauri.localhost",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

# Include routers
app.include_router(health.router)
app.include_router(watcher.router)
app.include_router(folders.router)


if __name__ == "__main__":
    # Redirect stdout and stderr to logger
    redirect_stdout_stderr(logger)
    
    # Configure and run server
    config = Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_config=None,  # Use our custom logging configuration
    )
    server = Server(config)
    
    logger.info("Starting sync microservice on port 8001")
    import asyncio
    asyncio.run(server.serve())
