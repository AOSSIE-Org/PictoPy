import logging

from fastapi import FastAPI
from uvicorn import Config, Server

from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware
from app.logging.setup_logging import get_sync_logger, configure_uvicorn_logging, setup_logging
from app.utils.logger_writer import redirect_stdout_stderr
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
    # 1. Setup logging before running the server
    setup_logging("sync-microservice")
    configure_uvicorn_logging("sync-microservice")
    config = Config(
        app=app,
        host="localhost",
        port=52124,
        log_level="info",
        log_config=None,  
    )
    server = Server(config)
    with redirect_stdout_stderr(
        logger, stdout_level=logging.INFO, stderr_level=logging.ERROR
    ):
        logger.info("Starting sync microservice on port 8001")
        import asyncio
        asyncio.run(server.serve())
