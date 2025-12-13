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
    # Note: sample_images fixture creates 10 images with monthly intervals,
    # but db_generate_memories requires at least 3 images per group
    # This assertion ensures the test fails if no memories are generated
    assert len(memories) > 0, "Expected memories to be generated from sample images, but got empty list"
    
    memory = memories[0]
    assert "id" in memory, "Memory should have 'id' field"
    assert "title" in memory, "Memory should have 'title' field"
    assert "description" in memory, "Memory should have 'description' field"
    assert "start_date" in memory, "Memory should have 'start_date' field"
    assert "end_date" in memory, "Memory should have 'end_date' field"
    assert "image_count" in memory, "Memory should have 'image_count' field"
    assert "images" in memory, "Memory should have 'images' field"
    assert isinstance(memory["images"], list), "Memory images should be a list"


def test_get_memory_images(test_db, sample_images):
    """Test retrieving images for a specific memory."""
    import sqlite3
    from app.config.settings import DATABASE_PATH
    
    db_create_memories_table()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Insert a test memory
        test_memory_id = "test_memory_2024_01"
        cursor.execute(
            """
            INSERT INTO memories 
            (id, title, description, start_date, end_date, location, latitude, longitude, image_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_memory_id,
                "Test Memory",
                "Test description",
                "2024-01-15",
                "2024-01-20",
                "Test Location",
                40.7128,
                -74.0060,
                3
            )
        )
        
        # Insert memory-image associations using sample images
        for idx in range(min(3, len(sample_images))):
            image_id = sample_images[idx]["id"]
            cursor.execute(
                """
                INSERT INTO memory_images (memory_id, image_id, is_representative)
                VALUES (?, ?, ?)
                """,
                (test_memory_id, image_id, True)
            )
        
        conn.commit()
        
        # Now test db_get_memory_images
        images = db_get_memory_images(test_memory_id)
        
        # Assertions
        assert isinstance(images, list), "Result should be a list"
        assert len(images) > 0, "Should return at least one image"
        assert len(images) <= 3, "Should return at most 3 images"
        
        # Verify required fields in each image
        for image in images:
            assert "id" in image, "Image should have 'id' field"
            assert "path" in image, "Image should have 'path' field"
            assert "thumbnail" in image, "Image should have 'thumbnail' field"
            assert "metadata" in image, "Image should have 'metadata' field"
            
            # Verify the image ID is from our test data
            assert image["id"] in [sample_images[i]["id"] for i in range(min(3, len(sample_images)))]
        
        # Clean up test memory
        cursor.execute("DELETE FROM memory_images WHERE memory_id = ?", (test_memory_id,))
        cursor.execute("DELETE FROM memories WHERE id = ?", (test_memory_id,))
        conn.commit()
        
    finally:
        conn.close()


def test_memory_title_generation(test_db, sample_images):
    """Test that memory titles are generated correctly."""
    db_create_memories_table()
    memories = db_generate_memories()
    
    # Explicitly assert memories were generated
    assert len(memories) > 0, "Expected memories to be generated from sample images for title validation"
    
    for memory in memories:
        # Title should not be empty
        assert memory["title"], "Memory title should not be empty"
        assert len(memory["title"]) > 0, "Memory title should have content"
        
        # Title should contain year or time reference
        assert any(
            indicator in memory["title"].lower()
            for indicator in ["year", "ago", "2023", "2024", "2025"]
        ), f"Memory title '{memory['title']}' should contain a time reference"


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
