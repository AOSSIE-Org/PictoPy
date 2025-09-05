"""
This module contains the main FastAPI application.
"""

# Standard library imports
import multiprocessing
import os
import json

# Third-party imports
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

# Utility imports
from app.utils.microservice import microservice_util_start_sync_service
from app.custom_logging import CustomizeLogger

# API route imports
from app.routes.folders import router as folders_router
from app.routes.albums import router as albums_router
from app.routes.images import router as images_router
from app.routes.face_clusters import router as face_clusters_router
from app.routes.user_preferences import router as user_preferences_router
from fastapi.openapi.utils import get_openapi
from app.custom_logging import CustomizeLogger


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
    microservice_util_start_sync_service()
    # Create ProcessPoolExecutor and attach it to app.state
    app.state.executor = ProcessPoolExecutor(max_workers=1)

    try:
        # Application is ready to serve requests
        yield
    finally:
        # Cleanup: Shutdown process pool gracefully
        app.state.executor.shutdown(wait=True)


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,  # Use our custom lifespan manager
    title="PictoPy",
    description="The API calls to PictoPy are done via HTTP requests. This backend is built using FastAPI.",
    contact={
        "name": "PictoPy Postman Collection",
        "url": "https://www.postman.com/aossie-pictopy/pictopy/overview",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Local Development server"}
    ],
)

# Initialize custom logger with configuration
app.logger = CustomizeLogger.make_logger("app/logging_config.json")


def generate_openapi_json():
    """
    Generate OpenAPI specification JSON file for API documentation.
    
    Creates a comprehensive OpenAPI schema that includes all routes, models,
    and metadata. The generated file is used for API documentation and
    client SDK generation.
    """
    try:
        # Generate OpenAPI schema from FastAPI app
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        # Add contact information to the schema
        openapi_schema["info"]["contact"] = app.contact

        # Determine output path for OpenAPI JSON file
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        openapi_path = os.path.join(
            project_root, "docs", "backend", "backend_python", "openapi.json"
        )

        # Ensure the directory exists
        os.makedirs(os.path.dirname(openapi_path), exist_ok=True)

        # Write the schema to file with proper formatting
        with open(openapi_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)
        app.logger.info(f"OpenAPI JSON generated at {openapi_path}")
    except Exception as e:
        app.logger.error(f"Failed to generate openapi.json: {e}")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Basic health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint to verify server status.
    
    Returns:
        dict: Simple status message confirming server is running
    """
    return {"message": "PictoPy Server is up and running!"}


# Register API routers with their respective prefixes and tags
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
    config = Config(app=app, host="0.0.0.0", port=8000, log_config=None)
    server = Server(config)
    
    # Start the server
    server.run()
