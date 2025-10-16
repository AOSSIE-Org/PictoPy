from fastapi import FastAPI
from uvicorn import Config, Server
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware
import os

# Load allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:1420,tauri://localhost"
).split(",")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="PictoPy Sync Microservice",
    description="File system synchronization service for PictoPy",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Only allow specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept"],
)
# Include route modules
app.include_router(health.router, prefix="/api/v1")
app.include_router(watcher.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")

if __name__ == "__main__":
    config = Config(app=app, host="0.0.0.0", port=8001, log_level="info")
    server = Server(config)
    server.run()
