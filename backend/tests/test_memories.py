"""
Tests for the Memories API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_images_with_metadata():
    """Sample images with metadata for testing."""
    return [
        {
            "id": "img1",
            "path": "/test/img1.jpg",
            "folder_id": "1",
            "thumbnailPath": "/thumb/img1.jpg",
            "metadata": {
                "date_created": "2023-06-15T10:00:00",
                "latitude": 26.9124,
                "longitude": 75.7873,
            },
            "isTagged": True,
            "isFavourite": False,
            "tags": None,
        },
        {
            "id": "img2",
            "path": "/test/img2.jpg",
            "folder_id": "1",
            "thumbnailPath": "/thumb/img2.jpg",
            "metadata": {
                "date_created": "2023-06-15T11:00:00",
                "latitude": 26.9125,
                "longitude": 75.7874,
            },
            "isTagged": True,
            "isFavourite": False,
            "tags": None,
        },
        {
            "id": "img3",
            "path": "/test/img3.jpg",
            "folder_id": "1",
            "thumbnailPath": "/thumb/img3.jpg",
            "metadata": {
                "date_created": "2022-06-15T10:00:00",
            },
            "isTagged": True,
            "isFavourite": False,
            "tags": None,
        },
    ]


@patch("app.routes.memories.generate_memories")
def test_get_memories_success(mock_generate_memories):
    """Test successful retrieval of memories."""
    mock_memories = [
        {
            "id": "memory1",
            "title": "Trip to Jaipur, 2023",
            "type": "trip",
            "date_range": {
                "start": "2023-06-15T10:00:00",
                "end": "2023-06-15T11:00:00",
            },
            "location": "Location (26.9124, 75.7873)",
            "media_count": 2,
            "representative_media": [
                {"id": "img1", "thumbnailPath": "/thumb/img1.jpg"},
            ],
            "media_ids": ["img1", "img2"],
        }
    ]
    mock_generate_memories.return_value = mock_memories

    response = client.get("/memories/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "memory1"
    assert data["data"][0]["title"] == "Trip to Jaipur, 2023"


@patch("app.routes.memories.generate_memories")
def test_get_memories_with_limit(mock_generate_memories):
    """Test getting memories with limit parameter."""
    mock_memories = [
        {"id": f"memory{i}", "title": f"Memory {i}", "type": "date_cluster",
         "date_range": {"start": "2023-01-01", "end": "2023-01-01"},
         "location": None, "media_count": 1,
         "representative_media": [], "media_ids": [f"img{i}"]}
        for i in range(10)
    ]
    mock_generate_memories.return_value = mock_memories

    response = client.get("/memories/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5


@patch("app.routes.memories.generate_memories")
def test_get_memories_empty(mock_generate_memories):
    """Test getting memories when none exist."""
    mock_generate_memories.return_value = []

    response = client.get("/memories/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 0


@patch("app.routes.memories.generate_memories")
def test_get_memory_by_id_success(mock_generate_memories):
    """Test getting a specific memory by ID."""
    mock_memories = [
        {
            "id": "memory1",
            "title": "Trip to Jaipur, 2023",
            "type": "trip",
            "date_range": {
                "start": "2023-06-15T10:00:00",
                "end": "2023-06-15T11:00:00",
            },
            "location": "Location (26.9124, 75.7873)",
            "media_count": 2,
            "representative_media": [
                {"id": "img1", "thumbnailPath": "/thumb/img1.jpg"},
            ],
            "media_ids": ["img1", "img2"],
        }
    ]
    mock_generate_memories.return_value = mock_memories

    response = client.get("/memories/memory1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "memory1"
    assert data["title"] == "Trip to Jaipur, 2023"


@patch("app.routes.memories.generate_memories")
def test_get_memory_by_id_not_found(mock_generate_memories):
    """Test getting a memory that doesn't exist."""
    mock_generate_memories.return_value = []

    response = client.get("/memories/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "Not Found"

