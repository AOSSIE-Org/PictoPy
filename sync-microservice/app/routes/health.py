"""
Health Check API Routes

This module provides health check endpoints for the PictoPy sync microservice.
It monitors the status of critical services including database connectivity
and file system watcher status.

Key Features:
- Database connection status monitoring
- File system watcher status verification
- Overall service health assessment
- Structured health response format
"""

# Third-party imports
from fastapi import APIRouter

# Application imports
from app.database.folders import db_check_database_connection
from app.utils.watcher import watcher_util_is_watcher_running
from app.schemas.health import HealthCheckResponse

# Create API router for health check endpoints
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for monitoring service status.
    
    This endpoint provides a comprehensive health status of the sync microservice,
    including database connectivity and file system watcher status. It's used
    by monitoring systems and load balancers to determine service availability.
    
    Returns:
        HealthCheckResponse: Structured response containing:
            - status: Overall service health (healthy/unhealthy)
            - database: Database connection status
            - watcher: File system watcher status
    """
    # Check database connection status
    db_status = db_check_database_connection()
    
    # Check file system watcher status
    watcher_status = watcher_util_is_watcher_running()
    
    # Determine overall service health
    overall_status = "healthy" if db_status and watcher_status else "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        database="connected" if db_status else "disconnected",
        watcher="running" if watcher_status else "stopped",
    )
