# API

The API calls to PictoPy are done via HTTP requests since we are hosting our backend on a FastAPI server. This was done to ensure low coupling between the frontend and the backend.
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
    "album_name": "string",
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

### Delete Multiple Images

- **Endpoint**: `DELETE /images/multiple-images`
- **Description**: Deletes multiple images from the system.
- **Request Format**:
  ```json
  {
    "paths": ["string", "string", ...],
    "isFromDevice": true
  }
  ```
- **Response**: Message confirming images deletion.

### Delete Folder

- **Endpoint**: `DELETE /images/delete-folder`
- **Description**: Deletes a folder and its images from the system (AI Tagging context).
- **Request Format**:
  ```json
  {
    "folder_path": "string"
  }
  ```
- **Response**: Message confirming folder deletion.

### Generate Thumbnails

- **Endpoint**: `POST /images/generate-thumbnails`
- **Description**: Generates thumbnails for images in a folder.
- **Request Format**:
  ```json
  {
    "folder_path": "string"
  }
  ```
- **Response**: Message confirming thumbnail generation.

### Get Thumbnail Path

- **Endpoint**: `GET /images/get-thumbnail-path`
- **Description**: Retrieves the path to the generated thumbnails folder.
- **Response**: JSON object containing the thumbnail folder path.

### Delete Thumbnails

- **Endpoint**: `DELETE /images/delete-thumbnails`
- **Description**: Deletes generated thumbnails for a folder.
- **Request Format**:
  ```json
  {
    "folder_path": "string"
  }
  ```
- **Response**: Message confirming thumbnail deletion.

### Add Folder Progress

- **Endpoint**: `GET /images/add-folder-progress`
- **Description**: Retrieves the progress of adding images from a folder.
- **Response**: JSON object containing progress information.

### Get All Image Objects

- **Endpoint**: `GET /images/all-image-objects`
- **Description**: Returns detailed metadata (dimensions, MIME type, tags) for every image.
- **Response**: JSON array of image objects.