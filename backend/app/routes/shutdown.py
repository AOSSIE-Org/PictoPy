import asyncio
import os
import signal
import functools
from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.microservice import microservice_util_stop_sync_service
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Shutdown"])


class ShutdownResponse(BaseModel):
    """Response model for shutdown endpoint."""

    status: str
    message: str
    sync_stopped: bool


async def _delayed_shutdown(delay: float = 0.5):
    """
    Shutdown the server after a short delay to allow the response to be sent.

    Args:
        delay: Seconds to wait before signaling shutdown
    """
    await asyncio.sleep(delay)
    logger.info("Backend shutdown initiated, exiting process...")

    # Send SIGTERM to self for graceful shutdown
    os.kill(os.getpid(), signal.SIGTERM)


@router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown():
    """
    Gracefully shutdown the PictoPy backend and sync microservice.

    This endpoint:
    1. Stops the sync microservice (via HTTP + process termination)
    2. Schedules backend server termination after response is sent
    3. Returns confirmation to the caller

    This is the primary shutdown mechanism - the frontend should call this
    endpoint when the application window is closed.

    Returns:
        ShutdownResponse with status, message, and sync_stopped flag
    """
    logger.info("Shutdown request received for PictoPy backend")

    sync_stopped = False

    # Stop the sync microservice first (run in executor to avoid blocking event loop)
    try:
        loop = asyncio.get_running_loop()
        sync_stopped = await loop.run_in_executor(
            None, functools.partial(microservice_util_stop_sync_service, timeout=3.0)
        )
        if not sync_stopped:
            logger.warning("Sync microservice may not have stopped cleanly")
    except Exception as e:
        logger.error(f"Error stopping sync microservice: {e}")

    # Define callback to handle potential exceptions in the background task
    def _handle_shutdown_exception(task: asyncio.Task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Shutdown task failed: {e}")

    # Schedule backend shutdown after response is sent
    shutdown_task = asyncio.create_task(_delayed_shutdown())
    shutdown_task.add_done_callback(_handle_shutdown_exception)

    return ShutdownResponse(
        status="shutting_down",
        message="PictoPy backend shutdown initiated. Sync service stopped.",
        sync_stopped=sync_stopped,
    )
