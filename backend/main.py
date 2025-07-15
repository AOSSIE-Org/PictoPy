"""
This module contains the main FastAPI application.
"""

from uvicorn import Config, Server
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.folders import db_create_folders_table

from app.routes.folders import router as folders_router
from app.routes.face_clusters import router as face_clusters_router
import multiprocessing


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and initialize systems
    db_create_YOLO_classes_table()
    db_create_clusters_table()  # Create clusters table first since faces references it
    db_create_faces_table()
    db_create_folders_table()
    db_create_images_table()

    # Create ProcessPoolExecutor and attach it to app.state
    app.state.executor = ProcessPoolExecutor()

    try:
        yield
    finally:
        app.state.executor.shutdown(wait=True)


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic health check endpoint
@app.get("/")
async def root():
    return {"message": "PictoPy Server is up and running!"}


app.include_router(folders_router, prefix="/folders", tags=["Folders"])
app.include_router(face_clusters_router, prefix="/face-clusters", tags=["Face Clusters"])


# Entry point for running with: python3 main.py
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows
    config = Config(app=app, host="0.0.0.0", port=8000, log_config=None)
    server = Server(config)
    server.run()
