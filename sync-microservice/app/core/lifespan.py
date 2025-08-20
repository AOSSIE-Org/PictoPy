from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.folders import (
    db_check_database_connection,
)
from app.utils.watcher import (
    watcher_util_start_folder_watcher,
    watcher_util_stop_folder_watcher,
)

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
        print("Starting PictoPy Sync Microservice...")

        # Check database connection
        if not db_check_database_connection():
            print("Failed to connect to PictoPy database")
            print(
                "Make sure the main PictoPy backend is set up and the database exists"
            )
            raise RuntimeError("Database connection failed")

        print("Database connection successful")

        watcher_started = watcher_util_start_folder_watcher()

        print("Sync microservice is ready!")

        yield

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt (Ctrl+C)")
        print("Initiating graceful shutdown...")
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        raise
    finally:
        # Shutdown
        print("Shutting down sync microservice...")
        if watcher_started:
            watcher_util_stop_folder_watcher()
            print("Folder watcher stopped")
        print("Shutdown complete")
