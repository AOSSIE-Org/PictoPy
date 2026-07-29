# Directory Structure

The entry point for the backend is in `main.py`, which initializes the databases and handles the startup and shutdown for the FastAPI server.

The code for the application mainly lies in the `app/` directory the hierarchy of which looks like this:

```bash
.
├── main.py
└── app/
    ├── config/
    ├── database/
    ├── models/
    ├── routes/
    ├── schemas/
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

| Name                  | Description                                                                                                                                                                                               |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`           | Handles operations related to photo albums, including creating, deleting, and managing albums and their contents.                                                                                         |
| `connection.py`       | `get_db_connection()` context manager: opens SQLite with the integrity PRAGMAs enabled, then commits or rolls back automatically.                                                                         |
| `face_clusters.py`    | Provides functions to create, insert, update, retrieve, and delete face cluster records along with related images.                                                                                        |
| `faces.py`            | Manages face-related data, including storing and retrieving face embeddings for facial recognition.                                                                                                       |
| `folders.py`          | Handles operations to create, insert, update, retrieve, and delete folder records, while handling folder hierarchies and AI tagging status.                                                               |
| `image_embeddings.py` | Stores/retrieves SigLIP2 image embeddings as float32 BLOBs, filtered by `model_version`; see [Semantic Search](semantic-search.md).                                                                       |
| `images.py`           | Deals with image-related operations, such as storing image metadata, managing image IDs, and handling image classifications.                                                                              |
| `memories.py`         | Creates the `memories`, `memory_images`, `memory_videos` and `memory_runs` tables and holds every memories query helper; see [Memories](memories.md).                                                     |
| `metadata.py`         | Manages the metadata and provides functions to create the table, retrieve stored metadata as a dictionary, and update the metadata with new values.                                                       |
| `semantic_labels.py`  | Creates and syncs the curated `semantic_labels` vocabulary (definitions plus cached label embeddings) and the `image_classes_display` view; its `event` labels drive the `semantic_event` memory trigger. |
| `video_frames.py`     | Stores sampled video keyframes, their embeddings and the tags derived from them.                                                                                                                          |
| `videos.py`           | Handles video records: table creation, bulk insert, and lookups by id, folder or index.                                                                                                                   |
| `yolo_mapping.py`     | Creates and manages mappings for YOLO object detection classes.                                                                                                                                           |

## models

This directory contains pre-trained machine learning models used in the application.

| Name                  | Description                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| `FaceDetector.py`     | a FaceDetector class for detecting faces in an image                                                     |
| `FaceNet.py`          | Pre-trained FaceNet model for generating face embeddings                                                 |
| `model_registry.py`   | `ModelSpec` definitions, model export paths, and lookups between model keys and file paths.              |
| `ObjectClassifier.py` | Detects objects in images and returns their class IDs                                                    |
| `ONNXSessionBase.py`  | Shared lazy-session/threading-lock/`session_registry` lifecycle for the two SigLIP2 model classes below. |
| `session_registry.py` | Reference-counts active ONNX sessions so a model is not deleted while in use.                            |
| `SigLIP2Text.py`      | Text-tower ONNX session; embeds a tokenized query into the same vector space as image embeddings.        |
| `SigLIP2Vision.py`    | Vision-tower ONNX session; embeds preprocessed images for storage in `image_embeddings`.                 |
| `YOLO.py`             | YOLO ONNX detects objects, outputs boxes.                                                                |

## routes

This directory contains API route definitions for different functionalities of the application.

| Name                  | Description                                                                                                                                                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`           | Handles API routes for album-related operations (create, delete, add/remove photos, view albums).                                                                                                                                        |
| `dependencies.py`     | Shared `get_state` FastAPI dependency, which hands routers the application state holding the process-pool executor.                                                                                                                      |
| `face_clusters.py`    | Rename clusters, list clusters, and fetch cluster images.                                                                                                                                                                                |
| `folders.py`          | Add, sync, update AI tagging, delete, and list folders, managing folder hierarchy and image processing asynchronously. Triggers the SigLIP2 embedding pass last, after YOLO/face processing (see [Semantic Search](semantic-search.md)). |
| `images.py`           | Deals with image-related operations (adding, deleting, retrieving images and their metadata), plus `GET /images/semantic-search` (see [Semantic Search](semantic-search.md)).                                                            |
| `memories.py`         | Router mounted at `/memories`: queue a curation run, report run status, fetch today's memory, list cards, fetch a full story, mark viewed/dismissed/notified, and delete a memory (see [Memories](memories.md)).                         |
| `models.py`           | Installs/uninstalls model tiers (including the `semantic` SigLIP2 bundle), reports install status, tracks SSE download progress, and exposes routes to get hardware recommendations.                                                     |
| `shutdown.py`         | Provides a single endpoint to gracefully terminate the PictoPy backend process on all platforms.                                                                                                                                         |
| `test.py`             | Legacy detection-test routes, fully commented out; kept for reference and not mounted.                                                                                                                                                   |
| `user_preferences.py` | Get and update user preferences stored in the metadata database.                                                                                                                                                                         |
| `videos.py`           | List videos, search them by tag, and run semantic search over video frames.                                                                                                                                                              |

## schemas

This directory contains Pydantic models defining the structure and validation of data exchanged through the API endpoints.

| Name                  | Description                                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `album.py`            | For validating and structuring album-related API requests.                                                            |
| `face_clusters.py`    | For requests and responses related to face cluster management.                                                        |
| `facetagging.py`      | Face matching, clustering, related images, and error responses.                                                       |
| `folders.py`          | Folder-related API requests, responses, and data structures                                                           |
| `images.py`           | Image management requests and responses, including deletions.                                                         |
| `memories.py`         | Memory cards, stories, and the generate/status/update/delete request and response models.                             |
| `test.py`             | Tests image detection requests, responses, and error handling.                                                        |
| `videos.py`           | Video listing and search responses, plus the shared error response.                                                   |
| `user_preferences.py` | User preferences API requests, responses, and error handling, including the `memories` block and its scoring weights. |

## utils

This directory contains utility functions and helper modules used across the application.

| Name                           | Description                                                                                                                                                           |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API.py`                       | Sends POST request to restart sync microservice, logs success or failure                                                                                              |
| `extract_location_metadata.py` | `MetadataExtractor`: pulls capture datetime and GPS coordinates, tagging each with the `date_source` it came from.                                                    |
| `face_clusters.py`             | Clusters face embeddings, updates clusters, generates cluster images.                                                                                                 |
| `faceSearch.py`                | Runs a face-similarity search for a supplied face and returns the matching images.                                                                                    |
| `face_quality.py`              | Quality gate deciding whether a detected face is good enough to cluster.                                                                                              |
| `FaceNet.py`                   | Preprocesses images, normalizes embeddings, computes similarity.                                                                                                      |
| `folders.py`                   | Manages folder trees: add, delete, sync folders in database and filesystem.                                                                                           |
| `hardware_detect.py`           | Detects GPU / Apple Silicon and derives the recommended model tier.                                                                                                   |
| `image_metadata.py`            | Extracts image metadata including EXIF,size,format, and creation date safely                                                                                          |
| `images.py`                    | Processes images in folders: thumbnails, detects faces, classifies,updates DB                                                                                         |
| `model_bootstrap.py`           | Ensures the models AI tagging needs are installed before a tagging pass starts.                                                                                       |
| `model_downloader.py`          | Downloads a model and verifies it against its expected SHA-256.                                                                                                       |
| `memory_curator.py`            | Runs the three memory triggers (anniversary, import event, semantic event) and the rescore entry points; see [Memories](memories.md).                                 |
| `memory_monitor.py`            | Profiling decorator logging a function's RAM usage and execution time (unrelated to the Memories feature).                                                            |
| `memory_scoring.py`            | Scores candidate images and videos from stored signals, then dedupes and time-spreads the survivors.                                                                  |
| `ONNX.py`                      | Returns ONNX execution providers list based on GPU acceleration preference.                                                                                           |
| `SigLIP.py`                    | Preprocesses images for SigLIP2, tokenizes search queries (with a thread-safe tokenizer cache), and caches the text-tower session across `/semantic-search` requests. |
| `semantic_labels.py`           | Syncs the curated vocabulary, builds label embeddings, and scores images and videos against them; see [Semantic Search](semantic-search.md).                          |
| `takeout_sidecar.py`           | Reads capture date and GPS from a Google Takeout sidecar JSON file next to an image or video.                                                                         |
| `video_capture_date.py`        | Reads capture timestamps straight out of MP4/MOV container boxes, without ffprobe.                                                                                    |
| `videos.py`                    | Processes videos in folders: validates, thumbnails, resolves capture dates, and updates the DB.                                                                       |
| `YOLO.py`                      | YOLO utilities for NMS, drawing, and model path from preferences.                                                                                                     |

## scripts

One-off maintenance scripts, outside the `app/` package (run manually, not part of the running application).

| Name                               | Description                                                                                                                                                                                                                            |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `build_eval_set.py`                | Downloads the calibration eval set from Wikimedia Commons.                                                                                                                                                                             |
| `build_semantic_vocabulary.py`     | Derives the semantic vocabulary seed from COCO, Places365 and Open Images.                                                                                                                                                             |
| `calibrate_semantic_vocabulary.py` | Bucket-calibrates the semantic vocabulary against the eval set.                                                                                                                                                                        |
| `reset_database.py`                | Deletes the SQLite database files so the next start rebuilds them from scratch.                                                                                                                                                        |
| `reset_embeddings.py`              | Wipes `image_embeddings` and resets `isEmbedded = 0` on all images, forcing a full re-embed on the next sync/tagging pass. Needed after any change to the embedding preprocessing pipeline that invalidates already-stored embeddings. |

The three vocabulary scripts read and write `scripts/vocabulary/`, which holds
the raw label candidates, the evaluation manifest and images, and the
calibration report.
