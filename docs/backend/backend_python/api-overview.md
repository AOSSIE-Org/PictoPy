# API Overview

Welcome to the PictoPy API documentation! This section provides comprehensive documentation for the PictoPy backend API, which is built using FastAPI and provides RESTful endpoints for image management, album operations, and face recognition features.

## What is PictoPy API?

PictoPy API is a RESTful web service that provides:

- **Image Management**: Upload, organize, and process images
- **Album Operations**: Create and manage photo albums
- **Face Recognition**: Detect and tag faces in images
- **Object Detection**: Identify objects in images using AI
- **Metadata Extraction**: Extract and manage image metadata

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: Database ORM for data persistence
- **OpenCV**: Computer vision and image processing
- **Face Recognition**: AI-powered face detection and clustering
- **YOLO**: Object detection in images

## API Structure

The API is organized into logical groups:

### 🧪 Test Endpoints (`/test`)
Health checks and system status endpoints for monitoring and debugging.

### 🖼️ Images (`/images`)
Complete image management including upload, processing, metadata extraction, and organization.

### 📁 Albums (`/albums`)
Album creation, management, and image organization features.

### 👤 Face Tagging (`/tag`)
AI-powered face detection, recognition, and tagging capabilities.

## Documentation Sections

### 📖 [API Documentation](api-documentation.md)
Comprehensive documentation of all API endpoints with detailed request/response examples.

### ⚡ [API Quick Reference](api-quick-reference.md)
Quick lookup table for all endpoints - perfect for developers who need fast access to endpoint information.

### 🎯 [Interactive Swagger UI](swagger-ui.md)
Guide to using the interactive Swagger documentation interface for testing and exploring the API.

### 🛠️ [Swagger Setup Guide](swagger-setup-guide.md)
Complete setup and usage guide for the Swagger documentation system.

## Getting Started

### 1. Start the Backend Server

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 2. Access the API

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### 3. Test the API

Start with the health check endpoint:
```bash
curl http://localhost:8000/test/health
```

## Key Features

### Automatic Documentation
FastAPI automatically generates interactive API documentation from your code, ensuring it's always up-to-date.

### Type Safety
All endpoints use Pydantic models for request/response validation, providing excellent type safety and automatic error handling.

### Interactive Testing
The Swagger UI allows you to test endpoints directly from your browser without needing external tools.

### Comprehensive Coverage
The API covers all aspects of image management, from basic operations to advanced AI features.

## Response Format

All API responses follow a consistent format:

```json
{
  "status": "success|error",
  "message": "Description of the operation result",
  "data": {} // Optional, contains response data
}
```

## Authentication

Currently, the API doesn't require authentication for local development. All endpoints are publicly accessible. In production environments, appropriate authentication mechanisms should be implemented.

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages:

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **404**: Not Found
- **422**: Validation Error
- **500**: Internal Server Error

## CORS Support

CORS is enabled for all origins to allow cross-origin requests from the frontend application.

## Development Workflow

1. **Start Server**: Always have the backend server running during development
2. **Use Swagger UI**: Test new endpoints immediately using the interactive documentation
3. **Check Logs**: Monitor server logs for debugging information
4. **Validate Schemas**: Ensure Pydantic models are correctly defined

## Examples

### Basic Usage

```bash
# Health check
curl http://localhost:8000/test/health

# Get all images
curl http://localhost:8000/images/all-images

# Create an album
curl -X POST http://localhost:8000/albums/create-album \
  -H "Content-Type: application/json" \
  -d '{"name": "Vacation Photos", "description": "Photos from my vacation"}'
```

### JavaScript/Fetch Examples

```javascript
// Get all albums
const response = await fetch('http://localhost:8000/albums/view-all');
const albums = await response.json();

// Upload an image
const formData = new FormData();
formData.append('file', imageFile);
const uploadResponse = await fetch('http://localhost:8000/images/upload', {
  method: 'POST',
  body: formData
});
```

## Next Steps

1. **Read the Documentation**: Start with the [API Documentation](api-documentation.md) for detailed endpoint information
2. **Use the Quick Reference**: Keep the [API Quick Reference](api-quick-reference.md) handy for fast lookups
3. **Explore with Swagger**: Use the [Interactive Swagger UI](swagger-ui.md) to test endpoints
4. **Set Up Your Environment**: Follow the [Swagger Setup Guide](swagger-setup-guide.md) for development setup

## Support

If you encounter any issues or have questions about the API:

1. Check the server logs for error messages
2. Use the Swagger UI to test endpoints and see detailed error responses
3. Refer to the troubleshooting section in the setup guide
4. Check the FastAPI documentation for general questions about the framework

---

The PictoPy API is designed to be intuitive, well-documented, and easy to use. The automatic documentation generation ensures that the documentation is always current with the actual implementation. 