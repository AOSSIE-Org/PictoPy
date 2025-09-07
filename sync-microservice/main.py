from fastapi import FastAPI
from uvicorn import Config, Server
from app.core.lifespan import lifespan
from app.routes import health, watcher, folders
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app with lifespan management
app = FastAPI(
    title="PictoPy Sync Microservice",
    description="File system synchronization service for PictoPy",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include route modules
app.include_router(health.router, prefix="/api/v1")
app.include_router(watcher.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")

if __name__ == "__main__":
    config = Config(app=app, host="0.0.0.0", port=8001, log_level="info")
    server = Server(config)
    server.run()
