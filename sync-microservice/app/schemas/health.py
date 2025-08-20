from pydantic import BaseModel
from typing import Literal


class HealthCheckResponse(BaseModel):
    """Health check endpoint response schema."""

    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]
    watcher: Literal["running", "stopped"]
