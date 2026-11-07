# Directory Structure

The entry point for the backend is in `main.py`, which initializes the databases and handles the startup and shutdown for the FastAPI server.

The code for the application mainly lies in the `app/` directory the hierarchy of which looks like this:

```bash
.
├── main.py
└── app/
    ├── config/
    ├── database/
    ├── logging/
    ├── models/
    ├── routes/
    ├── schemas/
    ├── share/
    └── utils/

```

We will discuss what each of these directories do and the relevant files they contain

## config

Related to variables used across the application.

| Name          | Description                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `settings.py` | Contains configuration files for the application, mainly paths and parameters which are used across the application |

## database

This directory contains files related to database operations, including table creation, query handling and some helper functions on the tables.
These files are the places where most of the SQL queries are written. By default, on startup this directory is where the databases (`.db` files) is
created.

| Name                  | Description                                                                                                                                                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`           | Handles operations related to photo albums, including creating, deleting, and managing albums and their contents.                                                                                                           |
| `connection.py`       | Provides the `get_db_connection` context manager, which opens a SQLite connection with strict integrity settings (foreign keys and CHECK constraints enforced) and automatically commits on success or rolls back on error. |
| `face_clusters.py`    | Provides functions to create, insert, update, retrieve, and delete face cluster records along with related images.                                                                                                          |
| `faces.py`            | Manages face-related data, including storing and retrieving face embeddings for facial recognition.                                                                                                                         |
| `folders.py`          | Handles operations to create, insert, update, retrieve, and delete folder records, while handling folder hierarchies and AI tagging status.                                                                                 |
| `image_embeddings.py` | Stores/retrieves SigLIP2 image embeddings as float32 BLOBs, filtered by `model_version`; see [Semantic Search](semantic-search.md).                                                                                         |
| `image_export.py`     | Reads everything metadata export writes for a batch of images, leaving out locked albums; see [Metadata Export](metadata-export.md).                                                                                        |
| `images.py`           | Deals with image-related operations, such as storing image metadata, managing image IDs, and handling image classifications.                                                                                                |
| `memories.py`         | Manages curated memories: creates the `memories`, `memory_images`, `memory_videos` and `memory_runs` tables and provides the queries to store, retrieve, score and clean up scored collections of photos and videos.        |
| `metadata.py`         | Manages the metadata and provides functions to create the table, retrieve stored metadata as a dictionary, and update the metadata with new values.                                                                         |
| `semantic_labels.py`  | Creates the (currently dormant) `semantic_labels`/`image_semantic_labels` tables reserved for a future curated-label browsing feature.                                                                                      |
| `video_frames.py`     | Manages the tables for sampled video keyframes, their embeddings and the video-level tags derived from them, kept separate from the images table so frames don't appear in the gallery, memories or face clustering.        |
| `videos.py`           | Handles video-related operations: creates the `videos` table (kept separate from images) and provides functions to insert, retrieve, delete and favourite video records.                                                    |
| `xmp_export_state.py` | The `image_xmp_state` table and the triggers that mark images needing a metadata export; see [Metadata Export](metadata-export.md).                                                                                         |
| `yolo_mapping.py`     | Creates and manages mappings for YOLO object detection classes.                                                                                                                                                             |

## logging

This directory contains centralized logging functionality used across the application, including custom formatting, color-coded log messages, environment-based configuration, and log handling for backend components, shared by the backend and the sync microservice.

| Name               | Description                                                                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `setup_logging.py` | Configures centralized logging, loads logging settings, provides named loggers, applies color-coded formatting, and intercepts Uvicorn and asyncio logs. |

## models

This directory contains pre-trained machine learning models used in the application.

| Name                  | Description                                                                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `FaceDetector.py`     | a FaceDetector class for detecting faces in an image                                                                                                               |
| `FaceNet.py`          | Pre-trained FaceNet model for generating face embeddings                                                                                                           |
| `model_registry.py`   | Defines the registry of ONNX models PictoPy uses (filename, download URL, checksum, size, feature and tier), the tier groupings, and where model files are stored. |
| `ObjectClassifier.py` | Detects objects in images and returns their class IDs                                                                                                              |
| `ONNXSessionBase.py`  | Shared lazy-session/threading-lock/`session_registry` lifecycle for the two SigLIP2 model classes below.                                                           |
| `session_registry.py` | Tracks which models currently have active sessions, so a model that is in use is not deleted and a model being deleted is not loaded.                              |
| `SigLIP2Text.py`      | Text-tower ONNX session; embeds a tokenized query into the same vector space as image embeddings.                                                                  |
| `SigLIP2Vision.py`    | Vision-tower ONNX session; embeds preprocessed images for storage in `image_embeddings`.                                                                           |
| `YOLO.py`             | YOLO ONNX detects objects, outputs boxes.                                                                                                                          |

## routes

This directory contains API route definitions for different functionalities of the application.

| Name                  | Description                                                                                                                                                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`           | Handles API routes for album-related operations (create, delete, add/remove photos, view albums).                                                                                                                                        |
| `config.py`           | Provides the endpoint that returns the file extensions (images and videos) the app can index and open.                                                                                                                                   |
| `dependencies.py`     | Provides helpers shared by the route modules: access to the application state, and a function that notifies the debounced metadata export after an edit.                                                                                 |
| `face_clusters.py`    | Rename clusters, list clusters, and fetch cluster images.                                                                                                                                                                                |
| `folders.py`          | Add, sync, update AI tagging, delete, and list folders, managing folder hierarchy and image processing asynchronously. Triggers the SigLIP2 embedding pass last, after YOLO/face processing (see [Semantic Search](semantic-search.md)). |
| `images.py`           | Deals with image-related operations (adding, deleting, retrieving images and their metadata), plus `GET /images/semantic-search` (see [Semantic Search](semantic-search.md)).                                                            |
| `memories.py`         | Provides endpoints to generate photo memories grouped by location and time, retrieve a timeline, and fetch on-this-day recollections.                                                                                                    |
| `metadata_export.py`  | Starts a library-wide metadata export and reports its status; see [Metadata Export](metadata-export.md).                                                                                                                                 |
| `models.py`           | Installs/uninstalls model tiers (including the `semantic` SigLIP2 bundle), reports install status, tracks SSE download progress, and exposes routes to get hardware recommendations.                                                     |
| `share.py`            | Handles the album sharing API: lists the network interfaces a share can be reached on, and lists, creates and revokes shares of albums.                                                                                                  |
| `shutdown.py`         | Provides a single endpoint to gracefully terminate the PictoPy backend process on all platforms.                                                                                                                                         |
| `user_preferences.py` | Get and update user preferences stored in the metadata database.                                                                                                                                                                         |
| `videos.py`           | Handles video-related routes: listing videos, searching by tag or semantic text search, scanning videos for faces and checking scan status, purging cached frames, and toggling favourites.                                              |

## schemas

This directory contains Pydantic models defining the structure and validation of data exchanged through the API endpoints.

| Name                  | Description                                                                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `album.py`            | For validating and structuring album-related API requests.                                                                                                         |
| `face_clusters.py`    | For requests and responses related to face cluster management.                                                                                                     |
| `facetagging.py`      | Face matching, clustering, related images, and error responses.                                                                                                    |
| `folders.py`          | Folder-related API requests, responses, and data structures                                                                                                        |
| `images.py`           | Image management requests and responses, including deletions.                                                                                                      |
| `memories.py`         | Requests and responses for the memories API: generating, listing, viewing, updating and deleting memories, today's memory, generation status, and error responses. |
| `metadata_export.py`  | Error response for the metadata export routes.                                                                                                                     |
| `share.py`            | Requests and responses for album sharing: creating, listing and revoking shares, available network interfaces, and error responses.                                |
| `test.py`             | Defines Pydantic request and response models for the legacy test routes.                                                                                           |
| `user_preferences.py` | User preferences API requests, responses, and error handling.                                                                                                      |
| `videos.py`           | Video data and metadata models, and the error response used by the video routes.                                                                                   |

## share

This directory contains the network album-sharing functionality of PictoPy, including share management, password protection, media access, HTTP routes, and sharing server configuration.

| Name          | Description                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app.py`      | Creates a separate FastAPI application for album sharing, registers share routes, and disables API documentation and OpenAPI endpoints.                                          |
| `media.py`    | Retrieves shared album information and image IDs, verifies album membership, and resolves image IDs to existing thumbnail or original image file paths.                          |
| `registry.py` | Manages active shares in memory, including token generation, expiration, revocation, password hashing, unlock authorization, and failed-password attempt throttling.             |
| `routes.py`   | Defines HTTP endpoints for viewing shared albums, unlocking password-protected shares, and serving thumbnails and original photographs with access control and cache validation. |
| `server.py`   | Manages the sharing server lifecycle, including socket binding, port selection, Uvicorn startup, asynchronous execution, and graceful shutdown.                                  |

## utils

This directory contains utility functions and helper modules used across the application.

| Name                           | Description                                                                                                                                                                                                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`                    | Handles album workflows involving multiple database tables, including converting memories into albums by retrieving associated photo IDs, validating album names, and creating albums with their photos.          |
| `API.py`                       | Sends a POST request to restart sync microservice, logs success or failure                                                                                                                                          |
| `extract_location_metadata.py` | Extracts GPS coordinates and capture datetime from image metadata JSON, supporting multiple metadata structures and date formats.                                                                                 |
| `face_clusters.py`             | Clusters face embeddings, updates clusters, generates cluster images.                                                                                                                                             |
| `face_quality.py`              | Evaluates detected faces based on confidence score, face size, and image sharpness to filter out low-quality faces before generating embeddings.                                                                  |
| `FaceNet.py`                   | Preprocesses images, normalizes embeddings, computes similarity.                                                                                                                                                  |
| `faceSearch.py`                | Searches by face: detects the face in a given image and finds matching images by comparing embeddings.                                                                                                            |
| `folders.py`                   | Manages folder trees: add, delete, sync folders in database and filesystem.                                                                                                                                       |
| `hardware_detect.py`           | Detects the machine's GPU, Apple Silicon and RAM to report hardware information and recommend a model tier.                                                                                                       |
| `image_metadata.py`            | Extracts image metadata including EXIF, size, format, and creation date safely                                                                                                                                      |
| `images.py`                    | Processes images in folders: thumbnails, detects faces, classifies, updates DB                                                                                                                                     |
| `memory_curator.py`            | Generates and manages ranked photo memories using anniversaries, import events, and AI-detected semantic events.                                                                                                  |
| `memory_monitor.py`            | Decorator logs memory usage and execution time of functions.                                                                                                                                                      |
| `memory_scoring.py`            | Scores and ranks photos using configurable signals, removes near-duplicates, filters outliers, and selects images spread across an event's timeline.                                                              |
| `model_bootstrap.py`           | Ensures the models needed for AI tagging (the selected YOLO tier and FaceNet) are downloaded.                                                                                                                     |
| `model_downloader.py`          | Downloads and verifies AI models using SHA-256 checksums, with resumable downloads, progress tracking, and retry handling.                                                                                        |
| `network.py`                   | Discovers and ranks the local network interfaces that share URLs can use.                                                                                                                                         |
| `ONNX.py`                      | Returns ONNX execution providers list based on GPU acceleration preference.                                                                                                                                       |
| `semantic_labels.py`           | Syncs the semantic label vocabulary, builds and caches label embeddings, and scores images and video keyframes to generate semantic tags.                                                                         |
| `share.py`                     | Orchestrates network album sharing by creating and revoking share tokens, managing the share server lifecycle, and providing share details and reachable URLs to the desktop UI.                                  |
| `SigLIP.py`                    | Preprocesses images for SigLIP2, tokenizes search queries (with a thread-safe tokenizer cache), and caches the text-tower session across `/semantic-search` requests.                                             |
| `takeout_sidecar.py`           | Extracts capture timestamps and GPS coordinates from Google Takeout sidecar JSON files when image EXIF metadata is missing.                                                                                       |
| `video_capture_date.py`        | Extracts capture and file creation timestamps from MP4/MOV container metadata without relying on external tools like FFmpeg.                                                                                      |
| `xmp/`                         | Metadata export: the metadata model, XMP codec, PNG container, export pass and edit debouncer; see [Metadata Export](metadata-export.md).                                                                         |
| `videos.py`                    | Processes and indexes videos by extracting metadata and thumbnails, sampling keyframes, detecting objects and faces, generating SigLIP2 embeddings, and managing video-related database records and frame caches. |
| `YOLO.py`                      | YOLO utilities for NMS, drawing, and model path from preferences.                                                                                                                                                 |

## scripts

One-off maintenance scripts, outside the `app/` package (run manually, not part of the running application).

| Name                  | Description                                                                                                                                                                                                                            |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reset_embeddings.py` | Wipes `image_embeddings` and resets `isEmbedded = 0` on all images, forcing a full re-embed on the next sync/tagging pass. Needed after any change to the embedding preprocessing pipeline that invalidates already-stored embeddings. |
