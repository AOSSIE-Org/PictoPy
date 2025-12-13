"""Database operations for the Memories feature.

This module handles all database operations related to generating and managing memories,
including time-based and location-based memory clustering.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def create_memories_table(conn: sqlite3.Connection):
    """Create the memories table if it doesn't exist.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            cover_image_id INTEGER,
            image_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_viewed TEXT,
            FOREIGN KEY (cover_image_id) REFERENCES images(id)
        )
        """
    )
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_images (
            memory_id INTEGER NOT NULL,
            image_id INTEGER NOT NULL,
            sequence_order INTEGER,
            PRIMARY KEY (memory_id, image_id),
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        )
        """
    )
    
    # Create indices for better query performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_date ON memories(start_date, end_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_location ON memories(latitude, longitude)"
    )
    
    conn.commit()
    logger.info("Memories tables created successfully")


def generate_time_based_memories(
    conn: sqlite3.Connection,
    reference_date: Optional[datetime] = None
) -> List[Dict]:
    """Generate time-based memories (e.g., 'On this day X years ago').
    
    Args:
        conn: SQLite database connection
        reference_date: The date to generate memories for (defaults to today)
    
    Returns:
        List of memory dictionaries
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    cursor = conn.cursor()
    memories = []
    
    # Generate memories for 1, 2, 3, 5, and 10 years ago
    years_ago_list = [1, 2, 3, 5, 10]
    
    for years_ago in years_ago_list:
        target_date = reference_date - timedelta(days=365 * years_ago)
        
        # Get images from the target date (+/- 7 days window)
        start_date = (target_date - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=7)).strftime("%Y-%m-%d")
        
        cursor.execute(
            """
            SELECT id, path, date_taken, latitude, longitude
            FROM images
            WHERE date_taken BETWEEN ? AND ?
            AND date_taken IS NOT NULL
            ORDER BY date_taken
            LIMIT 50
            """,
            (start_date, end_date)
        )
        
        images = cursor.fetchall()
        
        if images:
            # Create memory entry
            memory = {
                "type": "time_based",
                "title": f"On This Day {years_ago} {'Year' if years_ago == 1 else 'Years'} Ago",
                "description": f"Memories from {target_date.strftime('%B %d, %Y')}",
                "start_date": start_date,
                "end_date": end_date,
                "years_ago": years_ago,
                "image_count": len(images),
                "images": [
                    {
                        "id": img[0],
                        "path": img[1],
                        "date_taken": img[2],
                        "latitude": img[3],
                        "longitude": img[4]
                    }
                    for img in images
                ],
                "cover_image": {
                    "id": images[0][0],
                    "path": images[0][1]
                }
            }
            memories.append(memory)
    
    logger.info(f"Generated {len(memories)} time-based memories")
    return memories


def generate_location_based_memories(
    conn: sqlite3.Connection,
    min_images: int = 5,
    distance_threshold: float = 0.05
) -> List[Dict]:
    """Generate location-based memories by clustering images by geographic location.
    
    Args:
        conn: SQLite database connection
        min_images: Minimum number of images required to form a memory
        distance_threshold: Maximum distance in degrees for clustering (approx 5km)
    
    Returns:
        List of location-based memory dictionaries
    """
    cursor = conn.cursor()
    
    # Get all images with location data
    cursor.execute(
        """
        SELECT id, path, date_taken, latitude, longitude, location_name
        FROM images
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY date_taken
        """
    )
    
    images = cursor.fetchall()
    
    if not images:
        logger.info("No images with location data found")
        return []
    
    # Simple clustering by location proximity
    clusters = []
    used_images = set()
    
    for i, img in enumerate(images):
        if img[0] in used_images:
            continue
        
        cluster = [img]
        used_images.add(img[0])
        
        # Find nearby images
        for j in range(i + 1, len(images)):
            if images[j][0] in used_images:
                continue
            
            # Calculate approximate distance
            lat_diff = abs(img[3] - images[j][3])
            lon_diff = abs(img[4] - images[j][4])
            distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
            
            if distance <= distance_threshold:
                cluster.append(images[j])
                used_images.add(images[j][0])
        
        # Only create memory if cluster has enough images
        if len(cluster) >= min_images:
            clusters.append(cluster)
    
    # Convert clusters to memories
    memories = []
    for cluster in clusters:
        # Get date range
        dates = [img[2] for img in cluster if img[2]]
        if not dates:
            continue
        
        dates.sort()
        start_date = dates[0]
        end_date = dates[-1]
        
        # Get location name or generate one
        location_name = cluster[0][5] if cluster[0][5] else "Unknown Location"
        
        # Parse dates for title generation
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Generate title based on duration
            if (end_dt - start_dt).days <= 1:
                title = f"{location_name} - {start_dt.strftime('%B %d, %Y')}"
            else:
                title = f"Trip to {location_name}"
            
            description = f"{len(cluster)} photos from {start_dt.strftime('%B %Y')}"
        except Exception as e:
            logger.warning(f"Date parsing error: {e}")
            title = f"Memories at {location_name}"
            description = f"{len(cluster)} photos"
        
        memory = {
            "type": "location_based",
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "location": location_name,
            "latitude": cluster[0][3],
            "longitude": cluster[0][4],
            "image_count": len(cluster),
            "images": [
                {
                    "id": img[0],
                    "path": img[1],
                    "date_taken": img[2],
                    "latitude": img[3],
                    "longitude": img[4]
                }
                for img in cluster
            ],
            "cover_image": {
                "id": cluster[0][0],
                "path": cluster[0][1]
            }
        }
        memories.append(memory)
    
    logger.info(f"Generated {len(memories)} location-based memories")
    return memories


def save_memory(
    conn: sqlite3.Connection,
    memory_type: str,
    title: str,
    description: str,
    start_date: str,
    end_date: str,
    image_ids: List[int],
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> int:
    """Save a memory to the database.
    
    Args:
        conn: SQLite database connection
        memory_type: Type of memory ('time_based' or 'location_based')
        title: Memory title
        description: Memory description
        start_date: Start date of the memory period
        end_date: End date of the memory period
        image_ids: List of image IDs in this memory
        location: Location name (optional)
        latitude: Latitude coordinate (optional)
        longitude: Longitude coordinate (optional)
    
    Returns:
        The ID of the created memory
    """
    cursor = conn.cursor()
    
    # Insert memory
    cursor.execute(
        """
        INSERT INTO memories (
            memory_type, title, description, start_date, end_date,
            location, latitude, longitude, cover_image_id, image_count, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            memory_type, title, description, start_date, end_date,
            location, latitude, longitude, image_ids[0] if image_ids else None,
            len(image_ids), datetime.now().isoformat()
        )
    )
    
    memory_id = cursor.lastrowid
    
    # Insert memory-image associations
    for idx, image_id in enumerate(image_ids):
        cursor.execute(
            "INSERT INTO memory_images (memory_id, image_id, sequence_order) VALUES (?, ?, ?)",
            (memory_id, image_id, idx)
        )
    
    conn.commit()
    logger.info(f"Saved memory {memory_id}: {title}")
    return memory_id


def get_all_memories(conn: sqlite3.Connection) -> List[Dict]:
    """Get all saved memories from the database.
    
    Args:
        conn: SQLite database connection
    
    Returns:
        List of memory dictionaries with associated images
    """
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT 
            m.id, m.memory_type, m.title, m.description,
            m.start_date, m.end_date, m.location, m.latitude, m.longitude,
            m.cover_image_id, m.image_count, m.created_at, m.last_viewed
        FROM memories m
        ORDER BY m.start_date DESC
        """
    )
    
    memories = []
    for row in cursor.fetchall():
        memory_id = row[0]
        
        # Get images for this memory
        cursor.execute(
            """
            SELECT i.id, i.path, i.date_taken
            FROM memory_images mi
            JOIN images i ON mi.image_id = i.id
            WHERE mi.memory_id = ?
            ORDER BY mi.sequence_order
            """,
            (memory_id,)
        )
        
        images = [
            {"id": img[0], "path": img[1], "date_taken": img[2]}
            for img in cursor.fetchall()
        ]
        
        memories.append({
            "id": memory_id,
            "type": row[1],
            "title": row[2],
            "description": row[3],
            "start_date": row[4],
            "end_date": row[5],
            "location": row[6],
            "latitude": row[7],
            "longitude": row[8],
            "cover_image_id": row[9],
            "image_count": row[10],
            "created_at": row[11],
            "last_viewed": row[12],
            "images": images
        })
    
    return memories


def delete_memory(conn: sqlite3.Connection, memory_id: int) -> bool:
    """Delete a memory from the database.
    
    Args:
        conn: SQLite database connection
        memory_id: ID of the memory to delete
    
    Returns:
        True if successful, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    
    success = cursor.rowcount > 0
    if success:
        logger.info(f"Deleted memory {memory_id}")
    return success


def update_memory_viewed(conn: sqlite3.Connection, memory_id: int):
    """Update the last_viewed timestamp for a memory.
    
    Args:
        conn: SQLite database connection
        memory_id: ID of the memory
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memories SET last_viewed = ? WHERE id = ?",
        (datetime.now().isoformat(), memory_id)
    )
    conn.commit()
