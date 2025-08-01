# Swagger Documentation Setup Guide

This guide explains how to set up and use the Swagger API documentation for PictoPy.

## What is Swagger?

Swagger (OpenAPI) is a powerful tool for documenting REST APIs. FastAPI automatically generates interactive API documentation that allows you to:

- **Explore APIs**: Browse all available endpoints
- **Test APIs**: Execute requests directly from the browser
- **View Schemas**: See request/response data structures
- **Generate Code**: Export API specifications for client generation

## Automatic Documentation Generation

PictoPy uses FastAPI, which automatically generates Swagger documentation from your route definitions. The documentation is created from:

- **Route decorators**: `@app.get()`, `@app.post()`, etc.
- **Pydantic models**: Request/response schemas
- **Type hints**: Parameter types and validation
- **Docstrings**: Endpoint descriptions

## Accessing the Documentation

### 1. Install Documentation Dependencies

First, install the documentation dependencies:

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Or install from root requirements.txt
pip install -r requirements.txt
```

### 2. Start the Backend Server

Then, ensure the PictoPy backend is running:

```bash
# Navigate to the backend directory
cd backend

# Install backend dependencies (if not already done)
pip install -r requirements.txt

# Start the server
python main.py
```

The server will start on `http://localhost:8000`

### 2. Access Swagger UI

Open your browser and navigate to:
```
http://localhost:8000/docs
```

You should see the interactive Swagger UI interface.

### 3. Access ReDoc (Alternative)

For a different documentation interface, visit:
```
http://localhost:8000/redoc
```

## Using the Swagger UI

### Exploring Endpoints

1. **Browse Categories**: Endpoints are grouped by tags (Test, Images, Albums, Tagging)
2. **Expand Endpoints**: Click on any endpoint to see its details
3. **View Parameters**: See required and optional parameters
4. **Check Schemas**: View request/response data structures

### Testing Endpoints

1. **Click "Try it out"**: This enables interactive testing
2. **Fill Parameters**: Enter required parameters
3. **Execute Request**: Click "Execute" to send the request
4. **View Response**: See the actual response from the server

### Example: Testing the Health Check

1. Find the `/test/health` endpoint
2. Click "Try it out"
3. Click "Execute"
4. You should see a response like:
   ```json
   {
     "message": "Server is healthy!"
   }
   ```

## Understanding the Documentation

### Endpoint Information

Each endpoint shows:
- **HTTP Method**: GET, POST, PUT, DELETE
- **Path**: The endpoint URL
- **Description**: What the endpoint does
- **Parameters**: Required and optional parameters
- **Request Body**: For POST/PUT requests
- **Response**: Expected response format

### Parameter Types

- **Path Parameters**: Part of the URL (e.g., `{image_id}`)
- **Query Parameters**: URL query string (e.g., `?album_name=test`)
- **Request Body**: JSON data sent with the request
- **Form Data**: For file uploads

### Response Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **404**: Not Found
- **422**: Validation Error
- **500**: Internal Server Error

## Customizing Documentation

### Adding Descriptions

You can add descriptions to your endpoints using docstrings:

```python
@app.get("/images/all-images")
async def get_all_images():
    """
    Retrieve all images in the system.
    
    Returns a list of all images with their metadata including:
    - Image ID
    - File path
    - Creation date
    - File size
    """
    # Implementation here
```

### Using Pydantic Models

Define request/response models for better documentation:

```python
from pydantic import BaseModel

class AlbumCreate(BaseModel):
    name: str
    description: str = None

@app.post("/albums/create-album")
async def create_album(album: AlbumCreate):
    """
    Create a new album with the specified name and description.
    """
    # Implementation here
```

### Adding Tags

Group related endpoints using tags:

```python
@app.get("/images/all-images", tags=["Images"])
async def get_all_images():
    # Implementation here

@app.post("/albums/create-album", tags=["Albums"])
async def create_album():
    # Implementation here
```

## Troubleshooting

### Common Issues

1. **Server Not Running**
   - Ensure the backend server is started
   - Check that it's running on port 8000
   - Verify no other service is using the port

2. **CORS Issues**
   - The API has CORS enabled for all origins
   - If you're testing from a different domain, ensure CORS is properly configured

3. **Authentication Required**
   - Most endpoints don't require authentication in development
   - If you see authentication errors, check the endpoint requirements

4. **Validation Errors**
   - Check the request format matches the expected schema
   - Ensure all required parameters are provided
   - Verify data types are correct

### Debugging

1. **Check Server Logs**: Look at the terminal where the server is running
2. **Network Tab**: Use browser dev tools to see actual HTTP requests
3. **Response Details**: Swagger shows detailed error messages

## Best Practices

### For Developers

1. **Keep Documentation Updated**: Update docstrings when changing endpoints
2. **Use Descriptive Names**: Make endpoint names and parameters clear
3. **Provide Examples**: Include example requests/responses in docstrings
4. **Group Related Endpoints**: Use consistent tagging

### For API Users

1. **Start with Simple Endpoints**: Test health check and basic GET endpoints first
2. **Check Response Codes**: Always verify the response status
3. **Use the Schema**: Reference the request/response schemas for correct data formats
4. **Test with Real Data**: Use actual data when testing endpoints

## Integration with Development Workflow

### During Development

1. **Start Server**: Always have the server running during development
2. **Test Changes**: Use Swagger UI to test new endpoints immediately
3. **Validate Schemas**: Ensure Pydantic models are correctly defined
4. **Update Documentation**: Keep docstrings current with implementation

### For Production

1. **Disable Interactive Docs**: Consider disabling `/docs` in production
2. **Add Authentication**: Implement proper authentication for protected endpoints
3. **Rate Limiting**: Add rate limiting for production use
4. **Monitoring**: Monitor API usage and performance

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [ReDoc Documentation](https://github.com/Redocly/redoc)

---

The Swagger documentation is automatically generated and updated whenever you modify your FastAPI routes. Keep your code well-documented to ensure the generated documentation is comprehensive and useful. 