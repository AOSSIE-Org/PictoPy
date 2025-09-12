# Directory Structure

The entry point for the backend is in `main.py`, which initializes the databases and handles the startup and shutdown for the FastAPI server.

The code for the application mainly lies in the `app/` directory the heirarchy of which looks like this:

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

Related to variables used accross the application.

| Name          | Description                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `settings.py` | Contains configuration files for the application, mainly paths and parameters which are used across the application |

## database

This directory contains files related to database operations, including table creation, query handeling and some helper functions on the tables.
These files are the places where most of the SQL queries are written. By default, on startup this directory is where the databases (`.db` files) is
created.

| Name               | Description                                                                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`        | Handles operations related to photo albums, including creating, deleting, and managing albums and their contents.                                   |
| `face_clusters.py` | Provides functions to create, insert, update, retrieve, and delete face cluster records along with related images.                                  |
| `faces.py`         | Manages face-related data, including storing and retrieving face embeddings for facial recognition.                                                 |
| `folders.py`       | Handles operations to create, insert, update, retrieve, and delete folder records, while handling folder hierarchies and AI tagging status.         |
| `images.py`        | Deals with image-related operations, such as storing image metadata, managing image IDs, and handling image classifications.                        |
| `metadata.py`      | Manages the metadata and provides functions to create the table, retrieve stored metadata as a dictionary, and update the metadata with new values. |
| `yolo_mapping.py`  | Creates and manages mappings for YOLO object detection classes.                                                                                     |

## models

This directory contains pre-trained machine learning models used in the application.

| Name                  | Description                                              |
| --------------------- | -------------------------------------------------------- |
| `FaceDetector.py`     | a FaceDetector class for detecting faces in an image     |
| `FaceNet.py`          | Pre-trained FaceNet model for generating face embeddings |
| `ObjectClassifier.py` | Detects objects in images and returns their class IDs    |
| `YOLO.py`             | YOLO ONNX detects objects, outputs boxes.                |

## routes

This directory contains API route definitions for different functionalities of the application.

| Name                  | Description                                                                                                            |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `albums.py`           | Handles API routes for album-related operations (create, delete, add/remove photos, view albums)                       |
| `face_clusters.py`    | Rename clusters, list clusters, and fetch cluster images.                                                              |
| `facetagging.py`      | Manages routes for face matching, clustering, and finding related images                                               |
| `folders.py`          | Add, sync, update AI tagging, delete, and list folders, managing folder hierarchy and image processing asynchronously. |
| `images.py`           | Deals with image-related operations (adding, deleting, retrieving images and their metadata)                           |
| `user_preferences.py` | Get and update user preferences stored in the metadata database.                                                       |

## schemas

This directory contains Pydantic models defining the structure and validation of data exchanged through the API endpoints.

| Name                  | Description                                                     |
| --------------------- | --------------------------------------------------------------- |
| `album.py`            | For validating and structuring album-related API requests.      |
| `face_clusters.py`    | For requests and responses related to face cluster management.  |
| `facetagging.py`      | Face matching, clustering, related images, and error responses. |
| `folders.py`          | Folder-related API requests, responses, and data structures     |
| `images.py`           | Image management requests and responses, including deletions.   |
| `test.py`             | Tests image detection requests, responses, and error handling.  |
| `user_preferences.py` | User preferences API requests, responses, and error handling.   |

## utils

This directory contains utility functions and helper modules used across the application.

| Name                | Description                                                                   |
| ------------------- | ----------------------------------------------------------------------------- |
| `API.py`            | Sends POST request to restart sync microservice, logs success or failure      |
| `face_clusters.py`  | Clusters face embeddings, updates clusters, generates cluster images.         |
| `FaceNet.py`        | Preprocesses images, normalizes embeddings, computes similarity.              |
| `folders.py`        | Manages folder trees: add, delete, sync folders in database and filesystem.   |
| `image_metadata.py` | Extracts image metadata including EXIF,size,format, and creation date safely  |
| `images.py`         | Processes images in folders: thumbnails, detects faces, classifies,updates DB |
| `memory_monitor.py` | Decorator logs memory usage and execution time of functions.                  |
| `microservice.py`   | Starts sync microservice with virtual environment or bundled executable.      |
| `ONNX.py`           | Returns ONNX execution providers list based on GPU acceleration preference.   |
| `YOLO.py`           | YOLO utilities for NMS, drawing, and model path from preferences.             |
