import asyncio
import hmac
import os
import platform
import signal
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.config import settings
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

    # Clean up token file
    try:
        os.remove(settings.SHUTDOWN_TOKEN_FILE)
        logger.info("Shutdown token file removed")
    except OSError as e:
        logger.warning(f"Could not remove shutdown token file: {e}")

    if platform.system() == "Windows":
        # Windows: SIGTERM doesn't work reliably with uvicorn subprocesses
        os._exit(0)
    else:
        # Unix (Linux/macOS): SIGTERM allows cleanup handlers to run
        os.kill(os.getpid(), signal.SIGTERM)


@router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown(x_shutdown_token: Optional[str] = Header(default=None)):
    """Gracefully shutdown the PictoPy backend (requires X-Shutdown-Token)."""
    if x_shutdown_token is None:
        logger.warning("Shutdown attempt rejected: missing token")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Prevent timing-based token guessing
    if not hmac.compare_digest(x_shutdown_token, settings.SHUTDOWN_TOKEN):
        logger.warning("Shutdown attempt rejected: invalid token")
        raise HTTPException(status_code=403, detail="Forbidden")

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
