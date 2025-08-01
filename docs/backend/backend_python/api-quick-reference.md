# API Quick Reference

A quick reference guide for all PictoPy API endpoints.

## Base URL
```
http://localhost:8000
```

## Test Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/test/health` | Health check |
| GET | `/test/db` | Database connection test |

## Image Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/images/all-images` | Get all images |
| GET | `/images/{image_id}` | Get image by ID |
| POST | `/images/upload` | Upload image |
| DELETE | `/images/{image_id}` | Delete image |
| POST | `/images/generate-thumbnail` | Generate thumbnail |
| GET | `/images/{image_id}/metadata` | Get image metadata |

## Album Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/albums/create-album` | Create album |
| GET | `/albums/view-all` | Get all albums |
| GET | `/albums/view-album?album_name={name}` | Get album details |
| POST | `/albums/add-multiple-to-album` | Add images to album |
| DELETE | `/albums/remove-from-album` | Remove image from album |
| PUT | `/albums/edit-album-description` | Edit album description |
| DELETE | `/albums/delete-album` | Delete album |

## Face Recognition & Tagging

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tag/detect-faces` | Detect faces in image |
| GET | `/tag/face-clusters` | Get face clusters |
| POST | `/tag/tag-faces` | Tag faces with names |
| GET | `/tag/tagged-faces` | Get tagged faces |
| DELETE | `/tag/remove-tag` | Remove face tag |

## Common Request Bodies

### Create Album
```json
{
  "name": "string",
  "description": "string"
}
```

### Add Images to Album
```json
{
  "album_name": "string",
  "paths": ["string", "string", ...]
}
```

### Tag Faces
```json
{
  "cluster_id": "string",
  "name": "string"
}
```

## Response Format
```json
{
  "status": "success|error",
  "message": "string",
  "data": {}
}
```

## Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error 