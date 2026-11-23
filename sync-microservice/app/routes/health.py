from fastapi import APIRouter

from app.database.folders import db_check_database_connection
from app.schemas.health import HealthCheckResponse
from app.utils.watcher import watcher_util_is_watcher_running

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """Health check endpoint.

    Defined as a synchronous def function so FastAPI automatically offloads
    it to an external threadpool (run_in_threadpool), preventing blocking
    SQLite database I/O from starving the main asyncio event loop.
    """
    db_status = db_check_database_connection()
    return HealthCheckResponse(
        status="healthy" if db_status else "unhealthy",
        database="connected" if db_status else "disconnected",
        watcher="running" if watcher_util_is_watcher_running() else "stopped",
    )
