"""
Test to verify metadata is not double-parsed.
This test ensures the fix for double metadata parsing is working correctly.
"""

import pytest
from fastapi.testclient import TestClient
from app.database.images import db_get_all_images


def test_metadata_is_dict_from_database():
    """Test that db_get_all_images returns metadata as dict, not string."""
    result = db_get_all_images(limit=1)
    
    assert "images" in result
    assert "total" in result
    
    if result["total"] > 0:
        first_image = result["images"][0]
        assert "metadata" in first_image
        
        # Critical: metadata should be a dict, not a string
        assert isinstance(first_image["metadata"], dict), \
            f"Expected metadata to be dict, got {type(first_image['metadata'])}"
        
        # Verify it has expected keys
        metadata = first_image["metadata"]
        assert "name" in metadata
        assert "width" in metadata
        assert "height" in metadata


def test_api_endpoint_returns_valid_metadata(client):
    """Test that the /images endpoint returns properly structured metadata."""
    response = client.get("/images/?limit=1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    
    if data["total"] > 0:
        first_image = data["data"][0]
        
        # Metadata should be an object (dict) in JSON response
        assert "metadata" in first_image
        metadata = first_image["metadata"]
        
        # Should be a dict with expected structure
        assert isinstance(metadata, dict), \
            "Metadata should be a dict in JSON response"
        
        # Should have standard fields
        assert "name" in metadata
        assert "width" in metadata
        assert "height" in metadata
        assert "file_size" in metadata
        
        # Should NOT be a string that needs parsing
        assert not isinstance(metadata, str), \
            "Metadata should not be a JSON string"


@pytest.fixture
def client():
    """Create test client for API tests."""
    from fastapi import FastAPI
    from app.routes.images import router as images_router
    
    app = FastAPI()
    app.include_router(images_router, prefix="/images")
    
    return TestClient(app)
