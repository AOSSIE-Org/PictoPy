# API Documentation

This page provides comprehensive documentation for the PictoPy API endpoints. The API is built using FastAPI and provides RESTful endpoints for image management, album operations, and face recognition features.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API doesn't require authentication for local development. All endpoints are publicly accessible.

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "status": "success|error",
  "message": "Description of the operation result",
  "data": {} // Optional, contains response data
}
```

## API Endpoints

### Test Endpoints

#### Health Check
- **GET** `/test/health`
- **Description**: Check if the server is running
- **Response**: Simple status message

#### Test Database Connection
- **GET** `/test/db`
- **Description**: Test database connectivity
- **Response**: Database connection status

### Image Management

#### Get All Images
- **GET** `/images/all-images`
- **Description**: Retrieve all images in the system
- **Response**: List of image objects with metadata

#### Get Image by ID
- **GET** `/images/{image_id}`
- **Description**: Get specific image by ID
- **Parameters**: `image_id` (path parameter)
- **Response**: Image object with full metadata

#### Upload Image
- **POST** `/images/upload`
- **Description**: Upload a new image
- **Request**: Multipart form data with image file
- **Response**: Upload confirmation with image details

#### Delete Image
- **DELETE** `/images/{image_id}`
- **Description**: Delete an image by ID
- **Parameters**: `image_id` (path parameter)
- **Response**: Deletion confirmation

#### Generate Thumbnail
- **POST** `/images/generate-thumbnail`
- **Description**: Generate thumbnail for an image
- **Request**: JSON with image path
- **Response**: Thumbnail generation status

#### Get Image Metadata
- **GET** `/images/{image_id}/metadata`
- **Description**: Get detailed metadata for an image
- **Parameters**: `image_id` (path parameter)
- **Response**: Image metadata including EXIF data

### Album Management

#### Create Album
- **POST** `/albums/create-album`
- **Description**: Create a new album
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string" // optional
  }
  ```
- **Response**: Album creation confirmation

#### Get All Albums
- **GET** `/albums/view-all`
- **Description**: Retrieve all albums
- **Response**: List of album objects

#### Get Album Details
- **GET** `/albums/view-album`
- **Query Parameters**: `album_name` (string)
- **Description**: Get details and images in an album
- **Response**: Album details with image list

#### Add Images to Album
- **POST** `/albums/add-multiple-to-album`
- **Description**: Add multiple images to an album
- **Request Body**:
  ```json
  {
    "album_name": "string",
    "paths": ["string", "string", ...]
  }
  ```
- **Response**: Addition confirmation

#### Remove Image from Album
- **DELETE** `/albums/remove-from-album`
- **Description**: Remove an image from an album
- **Request Body**:
  ```json
  {
    "album_name": "string",
    "path": "string"
  }
  ```
- **Response**: Removal confirmation

#### Edit Album Description
- **PUT** `/albums/edit-album-description`
- **Description**: Update album description
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Response**: Update confirmation

#### Delete Album
- **DELETE** `/albums/delete-album`
- **Description**: Delete an album
- **Request Body**:
  ```json
  {
    "name": "string"
  }
  ```
- **Response**: Deletion confirmation

### Face Recognition and Tagging

#### Detect Faces in Image
- **POST** `/tag/detect-faces`
- **Description**: Detect faces in an image
- **Request**: JSON with image path
- **Response**: Face detection results

#### Get Face Clusters
- **GET** `/tag/face-clusters`
- **Description**: Get all face clusters
- **Response**: List of face clusters with associated images

#### Tag Faces
- **POST** `/tag/tag-faces`
- **Description**: Tag faces with names
- **Request Body**:
  ```json
  {
    "cluster_id": "string",
    "name": "string"
  }
  ```
- **Response**: Tagging confirmation

#### Get Tagged Faces
- **GET** `/tag/tagged-faces`
- **Description**: Get all tagged faces
- **Response**: List of tagged faces with names

#### Remove Face Tag
- **DELETE** `/tag/remove-tag`
- **Description**: Remove a face tag
- **Request Body**:
  ```json
  {
    "cluster_id": "string"
  }
  ```
- **Response**: Tag removal confirmation

## Error Handling

The API uses standard HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **404**: Not Found
- **500**: Internal Server Error

Error responses include:
```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

## Rate Limiting

Currently, there are no rate limits implemented. In production, consider implementing appropriate rate limiting.

## CORS

CORS is enabled for all origins to allow cross-origin requests from the frontend application.

## Examples

### Using curl

```bash
# Get all images
curl -X GET "http://localhost:8000/images/all-images"

# Create an album
curl -X POST "http://localhost:8000/albums/create-album" \
     -H "Content-Type: application/json" \
     -d '{"name": "Vacation Photos", "description": "Photos from my vacation"}'

# Upload an image
curl -X POST "http://localhost:8000/images/upload" \
     -F "file=@/path/to/image.jpg"

# Detect faces in an image
curl -X POST "http://localhost:8000/tag/detect-faces" \
     -H "Content-Type: application/json" \
     -d '{"image_path": "/path/to/image.jpg"}'
```

### Using JavaScript/Fetch

```javascript
// Get all albums
const response = await fetch('http://localhost:8000/albums/view-all');
const albums = await response.json();

// Create an album
const createAlbumResponse = await fetch('http://localhost:8000/albums/create-album', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'My Album',
    description: 'A collection of photos'
  })
});

// Upload an image
const formData = new FormData();
formData.append('file', imageFile);
const uploadResponse = await fetch('http://localhost:8000/images/upload', {
  method: 'POST',
  body: formData
});
```

## Interactive Documentation

For the most up-to-date and interactive API documentation, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation where you can test endpoints directly from your browser.

## Development

The API is built with:
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: Database ORM
- **OpenCV**: Image processing
- **Face Recognition**: Face detection and clustering

All endpoints are automatically documented through FastAPI's automatic documentation generation. 