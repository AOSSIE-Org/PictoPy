"""
This module contains the main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.images import create_images_table
from app.database.albums import create_albums_table
from app.routes.test import router as test_router
from app.routes.images import router as images_router
from app.routes.albums import router as albums_router


create_images_table()
create_albums_table()


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(test_router, prefix="/test", tags=["Test"])
app.include_router(images_router, prefix="/images", tags=["Images"])
app.include_router(albums_router, prefix="/albums", tags=["Albums"])