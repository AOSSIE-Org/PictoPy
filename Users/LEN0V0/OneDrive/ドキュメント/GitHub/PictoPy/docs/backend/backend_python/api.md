# API

The API calls to PictoPy are done via HTTP requests since we are hosting our backend on a Flask server. This was done to ensure low coupling between the frontend and the backend.
Follow this [Link](https://www.postman.com/cryosat-explorer-62744145/workspace/pictopy/overview) to get example request and response.

## Table of Contents

1. [Albums](#albums)
2. [Image](#image)
3. [Face Recognition and Tagging](#face-recognition-and-tagging)

## Albums

We briefly discuss the endpoints related to albums, all of these fall under the `/albums` route

### Create Album

- **Endpoint**: `POST /albums/create-album`
- **Description**: Creates a new album with the given name and optional description.
- **Request Format**:
  ```json
  {
    "name": "string",
    "description": "string" (optional)
  }
  ```
- **Response**: Message confirming album creation.

### Delete Album

- **Endpoint**: `DELETE /albums/delete-album`
- **Description**: Deletes an existing album by name.
- **Request Format**:
  ```json
  {
    "name": "string"
  }
  ```
- **Response**: Message confirming album deletion.

### Add Multiple Images to Album

- **Endpoint**: `POST /albums/add-multiple-to-album`
- **Description**: Adds multiple images to an existing album.
- **Request Format**:
  ```json
  {
    "album_name": "string",
    "paths": ["string", "string", ...]
  }
  ```
- **Response**: Message confirming images were added to the album.

### Remove Image from Album

- **Endpoint**: `DELETE /albums/remove-from-album`
- **Description**: Removes a single image from an album.
- **Request Format**:
  ```json
  {
    "album_name": "string",
    "path": "string"
  }
  ```
- **Response**: Message confirming image removal from the album.

### View Album Photos

- **Endpoint**: `GET /albums/view-album`
- **Description**: Retrieves all photos in a specified album.
- **Query Parameters**: `album_name` (string)
- **Response**: JSON object containing album name and list of photos.

### Edit Album Description

- **Endpoint**: `PUT /albums/edit-album-description`
- **Description**: Updates the description of an existing album.
- **Request Format**:
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Response**: Message confirming album description update.

### View All Albums

- **Endpoint**: `GET /albums/view-all`
- **Description**: Retrieves a list of all albums.
- **Response**: JSON object containing a list of all albums.

## Image

We briefly discuss the endpoints related to images, all of these fall under the `/images` route

### Get All Images

- **Endpoint**: `GET /images/all-images`
- **Description**: Retrieves a list of all image files in the system.
- **Response**: JSON object containing a list of image file paths.

### Add Multiple Images

- **Endpoint**: `POST /images/images`
- **Description**: Adds multiple images to the system and processes them in the background.
- **Request Format**:
  ```json
  {
    "paths": ["string", "string", ...]
  }
  ```
- **Response**: Message indicating that images are being processed.

### Delete Image

- **Endpoint**: `DELETE /images/delete-image`
- **Description**: Deletes a single image from the system.
- **Request Format**:
  ```json
  {
    "path": "string"
  }
  ```
- **Response**: Message confirming image deletion.

### Get All Image Objects

- **Endpoint**: `GET /images/all-image-objects`
- **Description**: Retrieves all images and their associated object classes.
- **Response**: JSON object mapping image paths to their object classes.

### Get Class IDs

- **Endpoint**: `GET /images/class-ids`
- **Description**: Retrieves the object classes for a specific image.
- **Query Parameters**: `path` (string) - full path to the image
- **Response**: JSON object containing the classes detected in the image.

### Add Folder

- **Endpoint**: `POST /images/add-folder`
- **Description**: Adds all images from a specified folder to the system and processes them in the background.
- **Request Format**:
  ```json
  {
    "folder_path": "string"
  }
  ```
- **Response**: Message indicating the number of images being processed from the folder.

## Face Recognition and Tagging

We briefly discuss the endpoints related to face tagging and recognition, all of these fall under the `/tag` route

### Face Matching

- **Endpoint**: `GET /tag/match`
- **Description**: Finds similar faces across all images in the database.
- **Response**: JSON object containing pairs of similar images and their similarity scores.

### Face Clusters

- **Endpoint**: `GET /tag/clusters`
- **Description**: Retrieves clusters of similar faces across all images.
- **Response**: JSON object containing clusters of images with similar faces.

### Related Images

- **Endpoint**: `GET /tag/related-images`
- **Description**: Finds images with faces related to the face in the given image.
- **Query Parameters**: `path` (string) - full path to the image
- **Response**: JSON object containing a list of related image paths.
