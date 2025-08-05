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
import os, json
from fastapi.openapi.utils import get_openapi



thumbnails_dir = os.path.join("images", "PictoPy.thumbnails")
os.makedirs(thumbnails_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app = FastAPI(
    lifespan=lifespan,
    title="API", 
    description="The API calls to PictoPy are done via HTTP requests since we are hosting our backend on a Flask server. This was done to ensure low coupling between the frontend and the backend.",
    contact={
        "name": "PictoPy Postman collection",
        "url": "https://www.postman.com/cryosat-explorer-62744145/workspace/pictopy/overview",
    },
    # It seems mkdocs does not allow dynamic editable URLs like plain swagger does.   
#this is necessary for apis to work . Need to add production endpoints here   
    servers=[
        {"url": "http://localhost:8000", "description": "Local Development server"},
        {"url": "https://aossie-org.github.io/PictoPy", "description": "Production server"}
    ],
    openapi_tags=[
        {
            "name": "Albums",
            "description": "We briefly discuss the endpoints related to albums, all of these fall under the /albums route"
        },
        {
            "name": "Images",
            "description": "We briefly discuss the endpoints related to images, all of these fall under the /images route"
        },
        {
            "name": "Tagging",
            "x-displayName": "Face recognition and Tagging",  
            "description": "We briefly discuss the endpoints related to face tagging and recognition, all of these fall under the /tag route"
        }
    ]
)

app.logger = CustomizeLogger.make_logger("app/logging_config.json")
def generate_openapi_json():
    try:
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers
            
        )
        openapi_schema["info"]["contact"]=app.contact
   
        


        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        openapi_path = os.path.join(project_root, "docs", "backend", "backend_python", "openapi.json")

        os.makedirs(os.path.dirname(openapi_path), exist_ok=True)

        with open(openapi_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)
        app.logger.info(f"OpenAPI JSON generated at {openapi_path}")
    except Exception as e:
        app.logger.error(f"Failed to generate openapi.json: {e}")


start_scheduler()


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

#Generate OpenAPI JSON file on all environments by all commands (python,fastapi,uvicorn)
generate_openapi_json()

# Trigger on production startup
@app.on_event("startup")
async def on_startup():
    generate_openapi_json()

# Runs when we use this command: python3 main.py (As in production)
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows.
    app.logger = CustomizeLogger.make_logger("app/logging_config.json")
    config = Config(app=app, host="0.0.0.0", port=8000, log_config=None)
    server = Server(config)
    server.run()
