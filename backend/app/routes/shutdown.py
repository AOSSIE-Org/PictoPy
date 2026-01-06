import asyncio
import os
import platform
import signal
from fastapi import APIRouter
from pydantic import BaseModel
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Shutdown"])


class ShutdownResponse(BaseModel):
    """Response model for shutdown endpoint."""

    status: str
    message: str


async def _delayed_shutdown(delay: float = 0.5):
    """
    Shutdown the server after a short delay to allow the response to be sent.

    Args:
        delay: Seconds to wait before signaling shutdown
    """
    await asyncio.sleep(delay)
    logger.info("Backend shutdown initiated, exiting process...")

    if platform.system() == "Windows":
        # Windows: SIGTERM doesn't work reliably with uvicorn subprocesses
        os._exit(0)
    else:
        # Unix (Linux/macOS): SIGTERM allows cleanup handlers to run
        os.kill(os.getpid(), signal.SIGTERM)


@router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown():
    """
    Gracefully shutdown the PictoPy backend.

    This endpoint schedules backend server termination after response is sent.
    The frontend is responsible for shutting down the sync service separately.

    Returns:
        ShutdownResponse with status and message
    """
    logger.info("Shutdown request received for PictoPy backend")

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
        message="PictoPy backend shutdown initiated.",
    )
