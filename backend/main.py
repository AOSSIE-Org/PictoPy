"""
This module contains the main FastAPI application.
"""

import multiprocessing
import os
import json

from uvicorn import Config, Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table
from app.database.albums import db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table

from app.routes.folders import router as folders_router
from app.routes.albums import router as albums_router
from app.routes.images import router as images_router
from app.routes.face_clusters import router as face_clusters_router
from app.routes.user_preferences import router as user_preferences_router
from fastapi.openapi.utils import get_openapi
from app.logging.setup_logging import (
    configure_uvicorn_logging,
    setup_logging,
    get_logger,
)

# Set up standard logging first
setup_logging("backend")

# Configure Uvicorn logging to use our custom formatter
configure_uvicorn_logging("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and initialize systems
    generate_openapi_json()
    db_create_folders_table()
    db_create_images_table()
    db_create_YOLO_classes_table()
    db_create_clusters_table()  # Create clusters table first since faces references it
    db_create_faces_table()
    db_create_albums_table()
    db_create_album_images_table()
    db_create_metadata_table()
    # Create ProcessPoolExecutor and attach it to app.state
    app.state.executor = ProcessPoolExecutor(max_workers=1)

    try:
        yield
    finally:
        app.state.executor.shutdown(wait=True)


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="PictoPy",
    description="The API calls to PictoPy are done via HTTP requests. This backend is built using FastAPI.",
    contact={
        "name": "PictoPy Postman Collection",
        "url": "https://www.postman.com/aossie-pictopy/pictopy/overview",
    },
    servers=[
        {"url": "http://localhost:52123", "description": "Local Development server"}
    ],
)


# Initialize logger for this module
logger = get_logger(__name__)


def generate_openapi_json():
    try:
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        openapi_schema["info"]["contact"] = app.contact

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        openapi_path = os.path.join(
            project_root, "docs", "backend", "backend_python", "openapi.json"
        )

        os.makedirs(os.path.dirname(openapi_path), exist_ok=True)

        with open(openapi_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)
        logger.info(f"OpenAPI JSON generated at {openapi_path}")
    except Exception as e:
        logger.error(f"Failed to generate openapi.json: {e}")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic health check endpoint
@app.get("/health", tags=["Health"])
async def root():
    return {"message": "PictoPy Server is up and running!"}


app.include_router(folders_router, prefix="/folders", tags=["Folders"])
app.include_router(albums_router, prefix="/albums", tags=["Albums"])
app.include_router(images_router, prefix="/images", tags=["Images"])
app.include_router(
    face_clusters_router, prefix="/face-clusters", tags=["Face Clusters"]
)
app.include_router(
    user_preferences_router, prefix="/user-preferences", tags=["User Preferences"]
)


# Entry point for running with: python3 main.py
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows
    logger = get_logger(__name__)
    logger.info("Starting PictoPy backend server...")

    # Create a simple config with log_config=None to disable Uvicorn's default logging
    config = Config(
        app=app,
        host="localhost",
        port=52123,
        log_level="info",
        log_config=None,  # This is crucial - disable Uvicorn's default logging config
    )
    server = Server(config)
    server.run()
