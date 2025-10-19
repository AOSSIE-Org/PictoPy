"""
This module contains the main FastAPI application.
"""

import multiprocessing
import os
import json

from uvicorn import Config, Server
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table
from app.database.albums import db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table
from app.utils.microservice import microservice_util_start_sync_service

from app.routes.folders import router as folders_router
from app.routes.albums import router as albums_router
from app.routes.images import router as images_router
from app.routes.face_clusters import router as face_clusters_router
from app.routes.user_preferences import router as user_preferences_router
from app.routes.auth import router as auth_router
from fastapi.openapi.utils import get_openapi
from app.config.settings import ALLOWED_ORIGINS, RATE_LIMIT_PER_MINUTE


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute"])


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
    # Create ProcessPoolExecutor with optimal worker count
    max_workers = max(1, multiprocessing.cpu_count() - 1)
    app.state.executor = ProcessPoolExecutor(max_workers=max_workers)

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
        {"url": "http://localhost:8000", "description": "Local Development server"}
    ],
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
        print(f"OpenAPI JSON generated at {openapi_path}")
    except Exception as e:
        print(f"Failed to generate openapi.json: {e}")


# Add security middleware - Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"],
)

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Only allow specific origins from config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "Accept",
    ],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Basic health check endpoint (no rate limit)
@app.get("/health", tags=["Health"])
@limiter.exempt
async def root():
    """Health check endpoint to verify server status."""
    return {
        "status": "healthy",
        "message": "PictoPy Server is up and running!",
        "version": app.version,
    }


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
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
    config = Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = Server(config)
    server.run()
