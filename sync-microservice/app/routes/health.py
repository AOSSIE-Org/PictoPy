from fastapi import APIRouter
from app.database.folders import db_check_database_connection
from app.utils.watcher import watcher_util_is_watcher_running
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    db_status = db_check_database_connection()
    return HealthCheckResponse(
        status="healthy" if db_status else "unhealthy",
        database="connected" if db_status else "disconnected",
        watcher="running" if watcher_util_is_watcher_running() else "stopped",
    )
