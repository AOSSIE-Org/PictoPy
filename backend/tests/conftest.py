import pytest
import os
import json
from datetime import datetime, timedelta

# Import database table creation functions
from app.database.faces import db_create_faces_table
from app.database.images import db_create_images_table, db_bulk_insert_images
from app.database.face_clusters import db_create_clusters_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.albums import db_create_albums_table, db_create_album_images_table
from app.database.folders import db_create_folders_table
from app.database.metadata import db_create_metadata_table
from app.database.memories import db_create_memories_table


@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    print("\n=== Running manual setup fixture ===")

    # Set test environment
    os.environ["TEST_MODE"] = "true"

    # Create all database tables in the same order as main.py
    print("Creating database tables...")
    try:
        db_create_YOLO_classes_table()
        db_create_clusters_table()  # Create clusters table first since faces references it
        db_create_faces_table()
        db_create_folders_table()
        db_create_albums_table()
        db_create_album_images_table()
        db_create_images_table()
        db_create_metadata_table()
        db_create_memories_table()
        print("All database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

    yield  # This is where the tests run

    # Teardown code runs after all tests
    print("\n=== Running cleanup after all tests ===")

    # Cleanup code here
    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]


@pytest.fixture
def test_db():
    """Fixture to provide a clean database for each test."""
    yield
    # Cleanup logic if needed


@pytest.fixture
def sample_images():
    """Fixture to create sample images with various dates for testing."""
    import sqlite3
    from app.config.settings import DATABASE_PATH
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Ensure tables exist
    db_create_folders_table()
    db_create_images_table()
    
    # Create a test folder
    cursor.execute(
        "INSERT OR IGNORE INTO folders (folder_id, path, AI_Tagging) VALUES (999, '/test/path', 1)"
    )
    
    # Create sample images with different dates
    sample_data = []
    base_date = datetime.now()
    
    for i in range(10):
        image_date = base_date - timedelta(days=i*30)  # Monthly intervals
        metadata = {
            "name": f"test_image_{i}.jpg",
            "date_created": image_date.isoformat(),
            "width": 1920,
            "height": 1080,
            "file_location": f"/test/path/image_{i}.jpg",
            "file_size": 102400,
            "item_type": "image/jpeg",
            "latitude": 40.7128 + (i * 0.01),
            "longitude": -74.0060 + (i * 0.01),
            "location": "New York"
        }
        
        sample_data.append({
            "id": f"test_image_{i}",
            "path": f"/test/path/image_{i}.jpg",
            "folder_id": 999,
            "thumbnailPath": f"/test/path/thumb_{i}.jpg",
            "metadata": json.dumps(metadata),
            "isTagged": False
        })
    
    # Insert sample images
    db_bulk_insert_images(sample_data)
    conn.commit()
    conn.close()
    
    yield sample_data
    
    # Cleanup
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE folder_id = 999")
    cursor.execute("DELETE FROM folders WHERE folder_id = 999")
    conn.commit()
    conn.close()


@pytest.fixture
def sample_images_with_location():
    """Fixture to create sample images with different locations for testing."""
    import sqlite3
    from app.config.settings import DATABASE_PATH
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Ensure tables exist
    db_create_folders_table()
    db_create_images_table()
    
    # Create a test folder
    cursor.execute(
        "INSERT OR IGNORE INTO folders (folder_id, path, AI_Tagging) VALUES (998, '/test/location', 1)"
    )
    
    # Create sample images with different locations
    locations = [
        ("New York", 40.7128, -74.0060),
        ("Los Angeles", 34.0522, -118.2437),
        ("Chicago", 41.8781, -87.6298),
    ]
    
    sample_data = []
    base_date = datetime.now()
    
    for i, (location, lat, lon) in enumerate(locations):
        for j in range(4):  # 4 images per location
            idx = i * 4 + j
            image_date = base_date - timedelta(days=idx*15)
            
            metadata = {
                "name": f"location_image_{idx}.jpg",
                "date_created": image_date.isoformat(),
                "width": 1920,
                "height": 1080,
                "file_location": f"/test/location/image_{idx}.jpg",
                "file_size": 102400,
                "item_type": "image/jpeg",
                "latitude": lat,
                "longitude": lon,
                "location": location
            }
            
            sample_data.append({
                "id": f"location_image_{idx}",
                "path": f"/test/location/image_{idx}.jpg",
                "folder_id": 998,
                "thumbnailPath": f"/test/location/thumb_{idx}.jpg",
                "metadata": json.dumps(metadata),
                "isTagged": False
            })
    
    # Insert sample images
    db_bulk_insert_images(sample_data)
    conn.commit()
    conn.close()
    
    yield sample_data
    
    # Cleanup
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE folder_id = 998")
    cursor.execute("DELETE FROM folders WHERE folder_id = 998")
    conn.commit()
    conn.close()
