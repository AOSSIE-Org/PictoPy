# Database

## Overview

PictoPy uses several SQLite databases to manage various aspects of the application. This document provides an overview of each database, its structure, and its primary operations.

!!! note "Database Engine"
All databases in PictoPy use SQLite, a lightweight, serverless database engine.

## Album Database

### File Location

The database path is defined in the configuration file as `ALBUM_DATABASE_PATH`.

### Table Structure

| Column Name  | Data Type | Constraints               | Description                    |
| ------------ | --------- | ------------------------- | ------------------------------ |
| album_name   | TEXT      | PRIMARY KEY               | Unique name of the album       |
| image_ids    | TEXT      |                           | JSON-encoded list of image IDs |
| description  | TEXT      |                           | Album description              |
| date_created | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation date of the album     |

### Functionality

The `albums.py` file contains functions for managing photo albums. It allows for creating and deleting albums, adding and removing photos from albums, retrieving album photos, editing album descriptions, and getting all albums.

!!! tip "JSON Encoding"
The `image_ids` field uses JSON encoding to store lists in a TEXT field.

## Faces Database

### File Location

The database path is defined in the configuration file as `FACES_DATABASE_PATH`.

### Table Structure

| Column Name | Data Type | Constraints               | Description                           |
| ----------- | --------- | ------------------------- | ------------------------------------- |
| id          | INTEGER   | PRIMARY KEY AUTOINCREMENT | Unique identifier for each face entry |
| image_id    | INTEGER   | FOREIGN KEY               | References image_id_mapping(id)       |
| embeddings  | TEXT      |                           | JSON-encoded face embeddings          |

### Functionality

The `faces.py` file manages face embeddings for images. It provides functionality for inserting and retrieving face embeddings, getting all face embeddings, deleting face embeddings for an image, and cleaning up orphaned face embeddings.

!!! warning "Referential Integrity"
The `image_id` column maintains referential integrity with the Images database.

## Images Database

### File Location

The database path is defined in the configuration file as `IMAGES_DATABASE_PATH`.

### Table Structures

#### 1. image_id_mapping

| Column Name | Data Type | Constraints               | Description                      |
| ----------- | --------- | ------------------------- | -------------------------------- |
| id          | INTEGER   | PRIMARY KEY AUTOINCREMENT | Unique identifier for each image |
| path        | TEXT      | UNIQUE                    | Absolute path to the image file  |

#### 2. images

| Column Name | Data Type | Constraints              | Description                     |
| ----------- | --------- | ------------------------ | ------------------------------- |
| id          | INTEGER   | PRIMARY KEY, FOREIGN KEY | References image_id_mapping(id) |
| class_ids   | TEXT      |                          | JSON-encoded class IDs          |
| metadata    | TEXT      |                          | JSON-encoded metadata           |

### Functionality

The `images.py` file manages image information, including paths, object classes, and metadata. It provides functions for inserting and deleting images, retrieving image paths and IDs, getting object classes for an image, and checking if an image is in the database.

!!! info "Path Handling"
The system uses absolute paths for image files to ensure consistency across different operations.

## YOLO Mappings Database

### File Location

The database path is defined in the configuration file as `MAPPINGS_DATABASE_PATH`.

### Table Structure

| Column Name | Data Type | Constraints | Description               |
| ----------- | --------- | ----------- | ------------------------- |
| class_id    | INTEGER   | PRIMARY KEY | YOLO class identifier     |
| name        | TEXT      | NOT NULL    | Human-readable class name |

### Functionality

The `yolo_mapping.py` file is responsible for creating and populating the mappings table with YOLO class names. This database stores mappings between YOLO class IDs and their corresponding names.

## Database Interactions

The databases in PictoPy interact with each other in the following ways:

1. The Albums database uses image IDs from the Images database to manage photos within albums.
2. The Faces database references image IDs from the Images database to associate face embeddings with specific images.
3. The Images database uses class IDs that correspond to the YOLO Mappings database for object recognition.

!!! example "Cross-Database Operation"
When adding a photo to an album, the system first checks if the image exists in the Images database, then adds its ID to the album in the Albums database.
