from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.folders import (
    db_check_database_connection,
)
from app.utils.watcher import (
    watcher_util_start_folder_watcher,
    watcher_util_stop_folder_watcher,
)
from app.logging.setup_logging import get_sync_logger

logger = get_sync_logger(__name__)

# Global variable to track watcher status
watcher_started = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifespan - startup and shutdown events.
    """
    global watcher_started

    try:
        # Startup
        logger.info("Starting PictoPy Sync Microservice...")

        # Check database connection
        if not db_check_database_connection():
            logger.error("Failed to connect to PictoPy database")
            logger.error(
                "Make sure the main PictoPy backend is set up and the database exists"
            )
            raise RuntimeError("Database connection failed")

        logger.info("Database connection successful")

        watcher_started = watcher_util_start_folder_watcher()

        logger.info("Sync microservice is ready!")

        yield

    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt (Ctrl+C)")
        logger.info("Initiating graceful shutdown...")
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down sync microservice...")
        if watcher_started:
            watcher_util_stop_folder_watcher()
            logger.info("Folder watcher stopped")
        logger.info("Shutdown complete")
