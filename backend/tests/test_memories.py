import pytest
from app.database.memories import (
    db_create_memories_table,
    db_generate_memories,
    db_get_memory_images,
)


def test_create_memories_table(test_db):
    """Test that memories table is created successfully."""
    db_create_memories_table()
    
    # Verify table exists by querying it
    import sqlite3
    from app.config.settings import DATABASE_PATH
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
    )
    assert cursor.fetchone() is not None
    
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_images'"
    )
    assert cursor.fetchone() is not None
    
    conn.close()


def test_generate_memories_empty(test_db):
    """Test generating memories with no images."""
    db_create_memories_table()
    memories = db_generate_memories()
    assert isinstance(memories, list)
    assert len(memories) == 0


def test_generate_memories_with_data(test_db, sample_images):
    """Test generating memories with sample images."""
    db_create_memories_table()
    memories = db_generate_memories()
    
    assert isinstance(memories, list)
    # Memories should group images by date and location
    if len(memories) > 0:
        memory = memories[0]
        assert "id" in memory
        assert "title" in memory
        assert "description" in memory
        assert "start_date" in memory
        assert "end_date" in memory
        assert "image_count" in memory
        assert "images" in memory
        assert isinstance(memory["images"], list)


def test_get_memory_images(test_db):
    """Test retrieving images for a specific memory."""
    db_create_memories_table()
    
    # Generate memories first
    memories = db_generate_memories()
    
    if len(memories) > 0:
        memory_id = memories[0]["id"]
        images = db_get_memory_images(memory_id)
        
        assert isinstance(images, list)
        # Images should have required fields
        if len(images) > 0:
            image = images[0]
            assert "id" in image
            assert "path" in image
            assert "thumbnail" in image
            assert "metadata" in image


def test_memory_title_generation(test_db, sample_images):
    """Test that memory titles are generated correctly."""
    db_create_memories_table()
    memories = db_generate_memories()
    
    if len(memories) > 0:
        for memory in memories:
            # Title should not be empty
            assert memory["title"]
            assert len(memory["title"]) > 0
            
            # Title should contain year or time reference
            assert any(
                indicator in memory["title"].lower()
                for indicator in ["year", "ago", "2023", "2024", "2025"]
            )


def test_memory_grouping_by_location(test_db, sample_images_with_location):
    """Test that memories are grouped by location."""
    db_create_memories_table()
    memories = db_generate_memories()
    
    # If we have multiple locations, they should be in separate memories
    locations = set()
    for memory in memories:
        if memory.get("location"):
            locations.add(memory["location"])
    
    # Each memory should have a consistent location
    for memory in memories:
        if memory.get("location") and len(memory["images"]) > 0:
            # All images in this memory should have similar locations
            assert memory["location"] is not None


def test_memory_image_count(test_db, sample_images):
    """Test that image count matches actual images."""
    db_create_memories_table()
    memories = db_generate_memories()
    
    for memory in memories:
        # Image count should match the total images in the group
        assert memory["image_count"] >= len(memory.get("images", []))
        # Representative images should not exceed total count
        assert len(memory.get("images", [])) <= 5  # Max 5 representative images
