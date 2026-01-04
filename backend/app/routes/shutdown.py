import asyncio
import os
import platform
import functools
from fastapi import APIRouter
from app.utils.microservice import cleanup_log_threads
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


def _final_kill_sync():
    """
    Final attempt to kill sync process by name right before backend exits.
    Uses os.system() for fully synchronous, blocking execution.
    Note: Using [P] trick to prevent pkill from matching itself.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            os.system("taskkill /F /IM PictoPy_Sync.exe >nul 2>&1")
        else:
            # Use [P] trick so pkill doesn't match itself
            os.system("pkill -9 -f '[P]ictoPy_Sync' 2>/dev/null")
            os.system("killall -9 PictoPy_Sync 2>/dev/null")
        logger.info("Final sync kill commands executed")
    except Exception as e:
        logger.warning(f"Final sync kill attempt: {e}")


async def _delayed_shutdown(delay: float = 0.5):
    """
    Shutdown the server after a short delay to allow the response to be sent.

    Args:
        delay: Seconds to wait before signaling shutdown
    """
    await asyncio.sleep(delay)
    logger.info("Backend shutdown initiated, exiting process...")

    # Clean up log threads before exit
    try:
        cleanup_log_threads()
    except Exception as e:
        logger.error(f"Error cleaning up log threads: {e}")

    # FINAL SAFETY: Kill sync by name right before we exit
    # This ensures sync dies even if all other methods failed
    _final_kill_sync()

    # Use os._exit(0) for immediate termination on all platforms
    # SIGTERM doesn't always work reliably with uvicorn
    os._exit(0)


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

    # KILL SYNC NOW - don't wait for delayed shutdown
    # This ensures sync dies before we return the response
    _final_kill_sync()

    # Define callback to handle potential exceptions in the background task
    def _handle_shutdown_exception(task: asyncio.Task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Shutdown task failed: {e}")

    # Schedule backend shutdown after response is sent
    shutdown_task = asyncio.create_task(_delayed_shutdown())
    shutdown_task.add_done_callback(_handle_shutdown_exception)

    message = (
        "PictoPy backend shutdown initiated. "
        f"Sync microservice {'stopped' if sync_stopped else 'stop attempted'}."
    )

    return ShutdownResponse(
        status="shutting_down",
        message=message,
        sync_stopped=sync_stopped,
    )
