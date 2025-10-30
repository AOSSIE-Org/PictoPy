import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.memories import router as memories_router

app = FastAPI()
app.include_router(memories_router, prefix="/memories")
client = TestClient(app)


def test_get_all_memories():
    """Test the /memories/all endpoint"""
    response = client.get("/memories/all")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "on_this_day" in data["data"]
    assert "recent" in data["data"]
    assert "people" in data["data"]
    assert "tags" in data["data"]


def test_get_on_this_day_memories():
    """Test the /memories/on-this-day endpoint"""
    response = client.get("/memories/on-this-day")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_on_this_day_memories_with_params():
    """Test the /memories/on-this-day endpoint with custom parameters"""
    response = client.get("/memories/on-this-day?years_back=3")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_recent_memories():
    """Test the /memories/recent endpoint"""
    response = client.get("/memories/recent")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_recent_memories_with_params():
    """Test the /memories/recent endpoint with custom parameters"""
    response = client.get("/memories/recent?days=7&min_images=3")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_people_memories():
    """Test the /memories/people endpoint"""
    response = client.get("/memories/people")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_people_memories_with_limit():
    """Test the /memories/people endpoint with custom limit"""
    response = client.get("/memories/people?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) <= 5


def test_get_tag_memories():
    """Test the /memories/tags endpoint"""
    response = client.get("/memories/tags")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_tag_memories_with_limit():
    """Test the /memories/tags endpoint with custom limit"""
    response = client.get("/memories/tags?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) <= 5


def test_invalid_years_back_parameter():
    """Test validation for years_back parameter"""
    response = client.get("/memories/on-this-day?years_back=0")
    assert response.status_code == 422  # Validation error


def test_invalid_days_parameter():
    """Test validation for days parameter"""
    response = client.get("/memories/recent?days=0")
    assert response.status_code == 422  # Validation error


def test_invalid_limit_parameter():
    """Test validation for limit parameter"""
    response = client.get("/memories/people?limit=0")
    assert response.status_code == 422  # Validation error
