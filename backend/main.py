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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager that handles application startup and shutdown events.
    On startup, it initializes database tables, cleans up face embeddings, 
    and initializes the face clustering system.
    On shutdown, it saves the current face cluster state to the database.
    """
    create_YOLO_mappings()
    create_faces_table()
    create_folders_table()
    create_images_table()
    create_image_id_mapping_table()
    create_albums_table()
    cleanup_face_embeddings()
    init_face_cluster()
    yield
    face_cluster = get_face_cluster()
    if face_cluster:
        face_cluster.save_to_db()


app = FastAPI(lifespan=lifespan)

start_scheduler()
# Starts the background scheduler to handle periodic or scheduled tasks.


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    """
    Root endpoint returning a simple JSON message confirming the server is running.
    """
    return {"message": "PictoPy Server is up and running!"}


app.include_router(test_router, prefix="/test", tags=["Test"])
app.include_router(images_router, prefix="/images", tags=["Images"])
app.include_router(albums_router, prefix="/albums", tags=["Albums"])
app.include_router(tagging_router, prefix="/tag", tags=["Tagging"])


# Runs when we use this command: python3 main.py (As in production)
if __name__ == "__main__":
    """
    Main entry point for running the FastAPI server using Uvicorn.
    Configures multiprocessing support for Windows, sets up logging, and runs the server.
    """
    multiprocessing.freeze_support()  # Required for Windows.
    app.logger = CustomizeLogger.make_logger("app/logging_config.json")
    config = Config(app=app, host="0.0.0.0", port=8000, log_config=None)
    server = Server(config)
    server.run()
