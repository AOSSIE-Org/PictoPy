import asyncio
import hmac
import os
import platform
import signal
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.config.settings import SHUTDOWN_TOKEN
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
async def shutdown(x_shutdown_token: str = Header(...)):
    """
    Gracefully shutdown the PictoPy backend.

    This endpoint requires the ``X-Shutdown-Token`` header to match the token
    generated at startup.  The token is shared with the Tauri frontend via a
    temporary file, so only the PictoPy application itself can trigger this
    endpoint — arbitrary local processes are rejected with 403 Forbidden.

    Returns:
        ShutdownResponse with status and message
    """
    # Use constant-time comparison to prevent timing-based token guessing
    if not hmac.compare_digest(x_shutdown_token, SHUTDOWN_TOKEN):
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
