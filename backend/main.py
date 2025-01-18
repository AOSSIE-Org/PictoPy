"""
This module contains the main FastAPI application.
"""

from uvicorn import Config, Server
from time import sleep
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing

from contextlib import asynccontextmanager

from app.database.faces import cleanup_face_embeddings, create_faces_table
from app.database.images import create_image_id_mapping_table, create_images_table
from app.database.albums import create_albums_table
from app.database.yolo_mapping import create_YOLO_mappings
from app.facecluster.init_face_cluster import get_face_cluster, init_face_cluster
from app.routes.test import router as test_router
from app.routes.images import router as images_router
from app.routes.albums import router as albums_router
from app.routes.facetagging import router as tagging_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_YOLO_mappings()
    create_faces_table()
    create_image_id_mapping_table()
    create_images_table()
    create_albums_table()
    cleanup_face_embeddings()
    init_face_cluster()
    yield
    face_cluster = get_face_cluster()
    if face_cluster:
        face_cluster.save_to_db()


app = FastAPI(lifespan=lifespan)

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
    return {"message": "PictoPy Server is up and running!"}


app.include_router(test_router, prefix="/test", tags=["Test"])
app.include_router(images_router, prefix="/images", tags=["Images"])
app.include_router(albums_router, prefix="/albums", tags=["Albums"])
app.include_router(tagging_router, prefix="/tag", tags=["Tagging"])


def run_server():
    config = Config(app=app, host="0.0.0.0", port=8000)
    server = Server(config)
    server.run()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows.
    run_server()