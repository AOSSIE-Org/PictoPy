from fastapi import FastAPI
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders

# Create FastAPI app with lifespan management
app = FastAPI(
    title="PictoPy Sync Microservice",
    description="File system synchronization service for PictoPy",
    version="1.0.0",
    lifespan=lifespan,
)

# Include route modules
app.include_router(health.router, prefix="/api/v1")
app.include_router(watcher.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")
