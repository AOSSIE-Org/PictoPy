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
- **Description**: Creates a new album with the given name, optional description, and optional hidden/password fields.
- **Request Format**:
  ```json
  {
    "name": "string",
    "description": "string" (optional),
    "is_hidden": true (optional),
    "password": "string" (optional)
  }
  ```
- **Response**: Message confirming album creation, with album details in a `data` field.

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
- **Description**: Retrieves all photos in a specified album. Supports password for hidden albums.
- **Query Parameters**: `album_name` (string), `password` (string, optional)
- **Response**: JSON object containing album name, list of photos, and `folder_path`.

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
- **Response**: JSON object containing `image_files` (list of file paths) and `folder_path`.

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

- **Endpoint**: `DELETE /images/multiple-images` *(Deprecated: Not present in current backend code)*
- **Description**: Deletes multiple images from the system. *(Deprecated)*

### Delete Folder

- **Endpoint**: `DELETE /images/delete-folder` *(Deprecated: Not present in current backend code)*
- **Description**: Deletes a folder and its images from the system (AI Tagging context). *(Deprecated)*

### Generate Thumbnails

- **Endpoint**: `POST /images/generate-thumbnails`
- **Description**: Generates thumbnails for images in one or more folders.
- **Request Format**:
  ```json
  {
    "folder_paths": ["string", "string", ...]
  }
  ```
- **Response**: Message confirming thumbnail generation, with failed paths if any.

### Get Thumbnail Path

- **Endpoint**: `GET /images/get-thumbnail-path` *(Deprecated: Not present in current backend code)*
- **Description**: Retrieves the path to the generated thumbnails folder. *(Deprecated)*

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

- **Endpoint**: `GET /images/add-folder-progress` *(Deprecated: Not present in current backend code)*
- **Description**: Retrieves the progress of adding images from a folder. *(Deprecated)*

### Get All Image Objects

- **Endpoint**: `GET /images/all-image-objects`
- **Description**: Returns detailed metadata (dimensions, MIME type, tags) for every image.
- **Response**: JSON object with `images` (dict of image path to classes/tags) and `image_path` (thumbnail path).

### Get Class IDs

- **Endpoint**: `GET /images/class-ids`
- **Description**: Returns class IDs (tags/objects) for a given image path.
- **Query Parameters**: `path` (string, required)
- **Response**: JSON object with class IDs or 'None'.

### Add Folder

- **Endpoint**: `POST /images/add-folder`
- **Description**: Adds one or more folders to the system for image management.
- **Request Format**:
  ```json
  {
    "folder_path": ["string", "string", ...]
  }
  ```
- **Response**: Message confirming folder addition.