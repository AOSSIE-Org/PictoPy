# Directory Structure

The entry point for the backend is in `main.py`, which initializes the databases and handles the startup and shutdown for the FastAPI server.

The code for the application mainly lies in the `app/` directory the heirarchy of which looks like this:

```bash
.
├── main.py
└── app/
    ├── config/
    ├── database/
    ├── facecluster/
    ├── facenet/
    ├── models/
    ├── routes/
    ├── utils/
    └── yolov8/

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

| Name              | Description                                                                                                                  |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `albums.py`       | Handles operations related to photo albums, including creating, deleting, and managing albums and their contents.            |
| `faces.py`        | Manages face-related data, including storing and retrieving face embeddings for facial recognition.                          |
| `images.py`       | Deals with image-related operations, such as storing image metadata, managing image IDs, and handling image classifications. |
| `yolo_mapping.py` | Creates and manages mappings for YOLO object detection classes.                                                              |

## facecluster

This directory contains files related to face clustering functionality, which is used to group similar faces together across different images.

| Name                   | Description                                                                    |
| ---------------------- | ------------------------------------------------------------------------------ |
| `init_face_cluster.py` | Initializes and manages the face clustering system                             |
| `facecluster.py`       | Implements the FaceCluster class, which handles the core face clustering logic |

## facenet

This directory contains files related to facial recognition functionality using FaceNet, a deep learning model for face embedding.

| Name            | Description                                                                   |
| --------------- | ----------------------------------------------------------------------------- |
| `facenet.py`    | Implements face detection and embedding generation using FaceNet and YOLOv8   |
| `preprocess.py` | Contains utility functions for image preprocessing and embedding manipulation |

## models

This directory contains pre-trained machine learning models used in the application.

| Name                | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `facenet.onnx`      | Pre-trained FaceNet model for generating face embeddings |
| `yolov8n-face.onnx` | YOLOv8 model trained specifically for face detection     |
| `yolov8n.onnx`      | YOLOv8 model for general object detection                |

## routes

This directory contains API route definitions for different functionalities of the application.

| Name             | Description                                                                                      |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| `albums.py`      | Handles API routes for album-related operations (create, delete, add/remove photos, view albums) |
| `facetagging.py` | Manages routes for face matching, clustering, and finding related images                         |
| `images.py`      | Deals with image-related operations (adding, deleting, retrieving images and their metadata)     |

## utils

This directory contains utility functions and helper modules used across the application.

| Name                 | Description                                                           |
| -------------------- | --------------------------------------------------------------------- |
| `classification.py`  | Provides functions for image classification using YOLOv8              |
| `metadata.py`        | Extracts and processes metadata from image files                      |
| `path_id_mapping.py` | Handles mappings between image paths and their database IDs           |
| `wrappers.py`        | Contains decorator functions for validating album and image existence |

## yolov8

This directory contains implementations and utilities for the YOLOv8 object detection model.
The code is taken from [This Repositry](https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection)

| Name        | Description                                                                                                      |
| ----------- | ---------------------------------------------------------------------------------------------------------------- |
| `utils.py`  | Provides utility functions for YOLOv8, including NMS, IoU computation, and drawing detections                    |
| `YOLOv8.py` | Implements the YOLOv8 class for object detection, including model initialization, inference, and post-processing |
