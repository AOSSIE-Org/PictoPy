# Swagger API Documentation

PictoPy uses FastAPI, which automatically generates interactive API documentation. The Swagger UI provides a comprehensive interface to explore and test all available API endpoints.

## Accessing the API Documentation

### Local Development
When running the PictoPy backend server locally, you can access the Swagger UI at:

```
http://localhost:8000/docs
```

### Interactive Documentation
The Swagger UI provides:
- **Interactive API Explorer**: Browse all available endpoints
- **Request/Response Examples**: See example requests and responses
- **Try It Out**: Test endpoints directly from the browser
- **Schema Documentation**: View detailed request/response schemas

## API Endpoints Overview

The PictoPy API is organized into the following categories:

### 🧪 Test Endpoints (`/test`)
- Health check and testing endpoints

### 🖼️ Images (`/images`)
- Image management and processing
- Thumbnail generation
- Image metadata extraction
- Object detection and classification

### 📁 Albums (`/albums`)
- Album creation and management
- Adding/removing images from albums
- Album metadata operations

### 👤 Face Tagging (`/tag`)
- Face detection and recognition
- Face clustering and grouping
- Face tagging operations

## Using the Swagger UI

1. **Start the Backend Server**: Ensure the PictoPy backend is running on port 8000
2. **Navigate to `/docs`**: Open your browser and go to `http://localhost:8000/docs`
3. **Explore Endpoints**: Click on any endpoint to expand its details
4. **Try Endpoints**: Use the "Try it out" button to test endpoints with your own data
5. **View Schemas**: Check the request/response schemas for detailed parameter information

## Alternative Documentation

FastAPI also provides ReDoc documentation at:
```
http://localhost:8000/redoc
```

ReDoc offers a different interface for viewing the same API documentation, often preferred for its cleaner, more readable format.

## API Authentication

Most endpoints in the current implementation don't require authentication for local development. However, in production environments, appropriate authentication mechanisms should be implemented.

## Example Usage

Here's a quick example of how to use the API:

```bash
# Get all images
curl -X GET "http://localhost:8000/images/all-images"

# Create an album
curl -X POST "http://localhost:8000/albums/create-album" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Album", "description": "A collection of photos"}'

# Get all albums
curl -X GET "http://localhost:8000/albums/view-all"
```

## Development Notes

- The API documentation is automatically generated from the FastAPI route definitions
- All endpoints include proper type hints and validation
- Request/response models are defined using Pydantic schemas
- CORS is enabled for cross-origin requests
- The server runs on port 8000 by default

---

> **Note**: Make sure the FastAPI server is running locally on port 8000 to access the interactive documentation.
