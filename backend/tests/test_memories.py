"""Unit tests for Memories feature."""

import pytest
import sqlite3
from datetime import datetime, timedelta
from app.database import memories as memories_db


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    conn = sqlite3.connect(':memory:')
    
    # Create images table (required for foreign keys)
    conn.execute("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY,
            path TEXT,
            date_taken TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT
        )
    """)
    
    # Create memories tables
    memories_db.create_memories_table(conn)
    
    yield conn
    conn.close()


@pytest.fixture
def sample_images(test_db):
    """Insert sample images for testing."""
    cursor = test_db.cursor()
    
    # Time-based test images (1 year ago)
    one_year_ago = datetime.now() - timedelta(days=365)
    for i in range(5):
        date = (one_year_ago + timedelta(days=i)).isoformat()
        cursor.execute(
            "INSERT INTO images (path, date_taken) VALUES (?, ?)",
            (f"/test/image_{i}.jpg", date)
        )
    
    # Location-based test images
    for i in range(10):
        cursor.execute(
            """INSERT INTO images (path, date_taken, latitude, longitude, location_name)
               VALUES (?, ?, ?, ?, ?)""",
            (
                f"/test/location_{i}.jpg",
                datetime.now().isoformat(),
                40.7128 + (i * 0.001),  # Nearby locations
                -74.0060 + (i * 0.001),
                "New York"
            )
        )
    
    test_db.commit()
    return test_db


def test_create_memories_table(test_db):
    """Test memories table creation."""
    cursor = test_db.cursor()
    
    # Check if tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
    )
    assert cursor.fetchone() is not None
    
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_images'"
    )
    assert cursor.fetchone() is not None


def test_generate_time_based_memories(sample_images):
    """Test time-based memory generation."""
    memories = memories_db.generate_time_based_memories(sample_images)
    
    # Should generate at least one memory for 1 year ago
    assert len(memories) >= 1
    
    # Check memory structure
    memory = memories[0]
    assert memory['type'] == 'time_based'
    assert 'title' in memory
    assert 'description' in memory
    assert 'images' in memory
    assert len(memory['images']) > 0


def test_generate_location_based_memories(sample_images):
    """Test location-based memory generation."""
    memories = memories_db.generate_location_based_memories(
        sample_images,
        min_images=5,
        distance_threshold=0.05
    )
    
    # Should generate at least one location-based memory
    assert len(memories) >= 1
    
    # Check memory structure
    memory = memories[0]
    assert memory['type'] == 'location_based'
    assert 'location' in memory
    assert 'latitude' in memory
    assert 'longitude' in memory
    assert len(memory['images']) >= 5


def test_save_memory(sample_images):
    """Test saving a memory to database."""
    memory_id = memories_db.save_memory(
        conn=sample_images,
        memory_type='time_based',
        title='Test Memory',
        description='Test description',
        start_date='2023-01-01',
        end_date='2023-01-31',
        image_ids=[1, 2, 3]
    )
    
    assert memory_id > 0
    
    # Verify memory was saved
    cursor = sample_images.cursor()
    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    memory = cursor.fetchone()
    assert memory is not None
    assert memory[2] == 'Test Memory'  # title column


def test_get_all_memories(sample_images):
    """Test retrieving all memories."""
    # Save a test memory
    memories_db.save_memory(
        conn=sample_images,
        memory_type='time_based',
        title='Test Memory',
        description='Test description',
        start_date='2023-01-01',
        end_date='2023-01-31',
        image_ids=[1, 2]
    )
    
    # Get all memories
    memories = memories_db.get_all_memories(sample_images)
    
    assert len(memories) >= 1
    assert memories[0]['title'] == 'Test Memory'
    assert len(memories[0]['images']) == 2


def test_delete_memory(sample_images):
    """Test deleting a memory."""
    # Save a test memory
    memory_id = memories_db.save_memory(
        conn=sample_images,
        memory_type='time_based',
        title='Test Memory',
        description='Test description',
        start_date='2023-01-01',
        end_date='2023-01-31',
        image_ids=[1]
    )
    
    # Delete the memory
    success = memories_db.delete_memory(sample_images, memory_id)
    assert success is True
    
    # Verify memory was deleted
    memories = memories_db.get_all_memories(sample_images)
    assert len(memories) == 0


def test_update_memory_viewed(sample_images):
    """Test updating memory viewed timestamp."""
    # Save a test memory
    memory_id = memories_db.save_memory(
        conn=sample_images,
        memory_type='time_based',
        title='Test Memory',
        description='Test description',
        start_date='2023-01-01',
        end_date='2023-01-31',
        image_ids=[1]
    )
    
    # Update viewed timestamp
    memories_db.update_memory_viewed(sample_images, memory_id)
    
    # Verify timestamp was updated
    memories = memories_db.get_all_memories(sample_images)
    assert memories[0]['last_viewed'] is not None


def test_location_clustering_threshold():
    """Test location clustering with different thresholds."""
    conn = sqlite3.connect(':memory:')
    conn.execute("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY,
            path TEXT,
            date_taken TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT
        )
    """)
    
    # Insert images at different distances
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO images (path, date_taken, latitude, longitude)
           VALUES (?, ?, ?, ?)""",
        ('/test/1.jpg', datetime.now().isoformat(), 40.7128, -74.0060)
    )
    cursor.execute(
        """INSERT INTO images (path, date_taken, latitude, longitude)
           VALUES (?, ?, ?, ?)""",
        ('/test/2.jpg', datetime.now().isoformat(), 40.7138, -74.0070)  # Close
    )
    cursor.execute(
        """INSERT INTO images (path, date_taken, latitude, longitude)
           VALUES (?, ?, ?, ?)""",
        ('/test/3.jpg', datetime.now().isoformat(), 41.0000, -75.0000)  # Far
    )
    conn.commit()
    
    memories_db.create_memories_table(conn)
    
    # Test with small threshold - should separate locations
    memories = memories_db.generate_location_based_memories(
        conn, min_images=2, distance_threshold=0.01
    )
    
    # With threshold of 0.01, close images should cluster, far one separate
    # But with min_images=2, only the close cluster should form a memory
    assert len(memories) <= 1
    
    conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
