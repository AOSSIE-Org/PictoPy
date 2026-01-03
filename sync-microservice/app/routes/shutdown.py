import asyncio
import os
import platform
import signal
from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.watcher import watcher_util_stop_folder_watcher
from app.logging.setup_logging import get_sync_logger

logger = get_sync_logger(__name__)

router = APIRouter(tags=["Shutdown"])


class ShutdownResponse(BaseModel):
    """Response model for shutdown endpoint."""

    status: str
    message: str


async def _delayed_shutdown(delay: float = 0.1):
    """
    Shutdown the server after a short delay to allow the response to be sent.

    Args:
        delay: Seconds to wait before signaling shutdown (kept minimal)
    """
    await asyncio.sleep(delay)
    logger.info("Exiting sync microservice...")

    if platform.system() == "Windows":
        os._exit(0)
    else:
        os.kill(os.getpid(), signal.SIGTERM)


@router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown():
    """
    Gracefully shutdown the sync microservice.

    This endpoint:
    1. Stops the folder watcher
    2. Schedules server termination after response is sent
    3. Returns confirmation to the caller

    Returns:
        ShutdownResponse with status and message
    """
    logger.info("Shutdown request received for sync microservice")

    try:
        # Stop the folder watcher first
        watcher_util_stop_folder_watcher()
    except Exception as e:
        logger.error(f"Error stopping folder watcher: {e}")

    # Define callback to handle potential exceptions in the background task
    def _handle_shutdown_exception(task: asyncio.Task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Sync shutdown task failed: {e}")

    # Schedule shutdown after response is sent
    shutdown_task = asyncio.create_task(_delayed_shutdown())
    shutdown_task.add_done_callback(_handle_shutdown_exception)

    return ShutdownResponse(
        status="shutting_down",
        message="Sync microservice shutdown initiated. Watcher stopped.",
    )
