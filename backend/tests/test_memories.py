import pytest
import uuid
from datetime import datetime
from app.database.memories import (
    db_create_memories_table,
    db_create_memory,
    db_get_all_memories,
    db_get_memory_by_id,
    db_update_memory_last_shown,
    db_delete_memory,
)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    db_create_memories_table()
    yield
    # Cleanup if needed


def test_create_memory(setup_database):
    """Test creating a memory"""
    memory_data = {
        "id": str(uuid.uuid4()),
        "title": "Test Memory",
        "description": "Test Description",
        "memory_type": "on_this_day",
        "date_range_start": datetime.now().isoformat(),
        "date_range_end": datetime.now().isoformat(),
        "image_count": 5,
        "created_at": datetime.now().isoformat(),
        "image_ids": [],
    }

    result = db_create_memory(memory_data)
    assert result is True


def test_get_all_memories(setup_database):
    """Test retrieving all memories"""
    memories = db_get_all_memories()
    assert isinstance(memories, list)


def test_get_memory_by_id(setup_database):
    """Test retrieving a specific memory"""
    # First create a memory
    memory_data = {
        "id": str(uuid.uuid4()),
        "title": "Test Memory for Retrieval",
        "memory_type": "location_trip",
        "date_range_start": datetime.now().isoformat(),
        "date_range_end": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    }
    db_create_memory(memory_data)
    
    # Retrieve it
    memory = db_get_memory_by_id(memory_data["id"])
    assert memory is not None
    assert memory["title"] == "Test Memory for Retrieval"


def test_update_memory_last_shown(setup_database):
    """Test updating last shown timestamp"""
    memory_data = {
        "id": str(uuid.uuid4()),
        "title": "Test Memory for Update",
        "memory_type": "on_this_day",
        "date_range_start": datetime.now().isoformat(),
        "date_range_end": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    }
    db_create_memory(memory_data)
    
    result = db_update_memory_last_shown(memory_data["id"])
    assert result is True


def test_delete_memory(setup_database):
    """Test deleting a memory"""
    memory_data = {
        "id": str(uuid.uuid4()),
        "title": "Test Memory for Deletion",
        "memory_type": "on_this_day",
        "date_range_start": datetime.now().isoformat(),
        "date_range_end": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    }
    db_create_memory(memory_data)
    
    result = db_delete_memory(memory_data["id"])
    assert result is True
    
    # Verify deletion
    memory = db_get_memory_by_id(memory_data["id"])
    assert memory is None
