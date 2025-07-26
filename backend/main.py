"""
This module contains the main FastAPI application.
"""

from uvicorn import Config, Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database.faces import cleanup_face_embeddings, create_faces_table
from app.database.images import create_image_id_mapping_table, create_images_table
from app.database.albums import create_albums_table
from app.database.yolo_mapping import create_YOLO_mappings
from app.database.folders import create_folders_table
from app.facecluster.init_face_cluster import get_face_cluster, init_face_cluster
from app.routes.test import router as test_router
from app.routes.images import router as images_router
from app.routes.albums import router as albums_router
from app.routes.facetagging import router as tagging_router
import multiprocessing
from app.scheduler import start_scheduler
from app.custom_logging import CustomizeLogger
import os


thumbnails_dir = os.path.join("images", "PictoPy.thumbnails")
os.makedirs(thumbnails_dir, exist_ok=True)

# Create directory for storing thumbnails if it does not exist


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This async context manager runs on app startup and shutdown
    # It initializes all required database tables and services on startup
    create_YOLO_mappings()
    create_faces_table()
    create_folders_table()
    create_images_table()
    create_image_id_mapping_table()
    create_albums_table()
    cleanup_face_embeddings()
    init_face_cluster()
    yield
    # On shutdown, save the current state of the face cluster to the database if it exists
    face_cluster = get_face_cluster()
    if face_cluster:
        face_cluster.save_to_db()


app = FastAPI(lifespan=lifespan)

# Start the background scheduler when the app starts
start_scheduler()


# Add CORS middleware to allow cross-origin requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all HTTP headers
)


@app.get("/")
async def root():
    # Root endpoint that returns a simple status message indicating the server is running
    return {"message": "PictoPy Server is up and running!"}


# Include routers for different API route groups with prefixes and tags
app.include_router(test_router, prefix="/test", tags=["Test"])
app.include_router(images_router, prefix="/images", tags=["Images"])
app.include_router(albums_router, prefix="/albums", tags=["Albums"])
app.include_router(tagging_router, prefix="/tag", tags=["Tagging"])


# Runs the server when this script is executed directly (typically in production)
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for compatibility with Windows multiprocessing
    app.logger = CustomizeLogger.make_logger("app/logging_config.json")
    config = Config(app=app, host="0.0.0.0", port=8000, log_config=None)
    server = Server(config)
    server.run()
