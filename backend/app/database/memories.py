# Standard library imports
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# App-specific imports
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_memories_table() -> None:
    """Create the memories table to cache generated memories."""
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            image_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Junction table for memory-image relationships
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_images (
            memory_id TEXT,
            image_id TEXT,
            is_representative BOOLEAN DEFAULT 0,
            PRIMARY KEY (memory_id, image_id),
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    conn.close()


def db_generate_memories() -> List[Dict[str, Any]]:
    """
    Generate memories by grouping images based on time and location.
    Returns a list of memory objects with representative images.
    """
    conn = _connect()
    cursor = conn.cursor()

    try:
        # Get all images with metadata
        cursor.execute(
            """
            SELECT id, path, thumbnailPath, metadata, folder_id
            FROM images
            ORDER BY json_extract(metadata, '$.date_created') DESC
            """
        )
        
        images = cursor.fetchall()
        
        if not images:
            return []

        # Parse images and group by date and location
        from app.utils.images import image_util_parse_metadata
        
        memories_by_group = defaultdict(list)
        
        for image_id, path, thumbnail, metadata_str, folder_id in images:
            metadata = image_util_parse_metadata(metadata_str)
            
            # Extract date and location
            date_created = metadata.get("date_created")
            if not date_created:
                continue
                
            # Parse date (format: YYYY-MM-DD HH:MM:SS or ISO format)
            try:
                if "T" in date_created:
                    date_obj = datetime.fromisoformat(date_created.replace("Z", "+00:00"))
                else:
                    date_obj = datetime.strptime(date_created.split()[0], "%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Could not parse date {date_created}: {e}")
                continue
            
            location = metadata.get("location", "Unknown Location")
            latitude = metadata.get("latitude")
            longitude = metadata.get("longitude")
            
            # Create grouping key (year-month + location)
            date_key = date_obj.strftime("%Y-%m")
            
            # Group by similar locations (or "Unknown")
            loc_key = location if location != "Unknown Location" else "no_location"
            
            group_key = f"{date_key}_{loc_key}"
            
            memories_by_group[group_key].append({
                "id": image_id,
                "path": path,
                "thumbnail": thumbnail,
                "date": date_obj,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "metadata": metadata
            })
        
        # Generate memory objects
        memories = []
        current_date = datetime.now()
        
        for group_key, images_in_group in memories_by_group.items():
            if len(images_in_group) < 3:  # Skip groups with too few images
                continue
                
            # Sort images by date
            images_in_group.sort(key=lambda x: x["date"])
            
            first_date = images_in_group[0]["date"]
            last_date = images_in_group[-1]["date"]
            location = images_in_group[0]["location"]
            
            # Calculate time difference
            time_diff = current_date - first_date
            years_ago = time_diff.days // 365
            
            # Generate title based on time
            if years_ago == 0:
                month_name = first_date.strftime("%B")
                title = f"{month_name} {first_date.year}"
            elif years_ago == 1:
                title = f"One Year Ago - {first_date.strftime('%B %Y')}"
            else:
                title = f"{years_ago} Years Ago - {first_date.strftime('%B %Y')}"
            
            # Add location to title if available
            if location and location != "Unknown Location":
                title = f"{title} • {location}"
            
            # Generate description
            description = f"{len(images_in_group)} photos from {first_date.strftime('%b %d')} to {last_date.strftime('%b %d, %Y')}"
            
            # Select representative images (first 5)
            representative_images = images_in_group[:5]
            
            memory = {
                "id": group_key,
                "title": title,
                "description": description,
                "start_date": first_date.isoformat(),
                "end_date": last_date.isoformat(),
                "location": location,
                "latitude": images_in_group[0]["latitude"],
                "longitude": images_in_group[0]["longitude"],
                "image_count": len(images_in_group),
                "images": representative_images,
                "all_image_ids": [img["id"] for img in images_in_group]
            }
            
            memories.append(memory)
        
        # Sort memories by most recent first
        memories.sort(key=lambda x: x["start_date"], reverse=True)
        
        # Persist memories to database
        try:
            # Clear old memories
            cursor.execute("DELETE FROM memory_images")
            cursor.execute("DELETE FROM memories")
            
            # Insert new memories
            for memory in memories:
                cursor.execute(
                    """
                    INSERT INTO memories 
                    (id, title, description, start_date, end_date, location, latitude, longitude, image_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory["id"],
                        memory["title"],
                        memory["description"],
                        memory["start_date"],
                        memory["end_date"],
                        memory["location"],
                        memory["latitude"],
                        memory["longitude"],
                        memory["image_count"]
                    )
                )
                
                # Insert memory-image associations
                for idx, image_id in enumerate(memory["all_image_ids"]):
                    is_representative = idx < 5  # First 5 are representative
                    cursor.execute(
                        """
                        INSERT INTO memory_images (memory_id, image_id, is_representative)
                        VALUES (?, ?, ?)
                        """,
                        (memory["id"], image_id, is_representative)
                    )
            
            conn.commit()
            logger.info(f"Successfully persisted {len(memories)} memories to database")
        except Exception as e:
            logger.error(f"Error persisting memories: {e}")
            conn.rollback()
        
        return memories
        
    except Exception as e:
        logger.error(f"Error generating memories: {e}")
        return []
    finally:
        conn.close()


def db_get_memory_images(memory_id: str) -> List[Dict[str, Any]]:
    """
    Get all images associated with a specific memory.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT i.id, i.path, i.thumbnailPath, i.metadata
            FROM images i
            JOIN memory_images mi ON i.id = mi.image_id
            WHERE mi.memory_id = ?
            ORDER BY json_extract(i.metadata, '$.date_created') ASC
            """,
            (memory_id,)
        )
        
        images = []
        from app.utils.images import image_util_parse_metadata
        
        for image_id, path, thumbnail, metadata_str in cursor.fetchall():
            metadata = image_util_parse_metadata(metadata_str)
            images.append({
                "id": image_id,
                "path": path,
                "thumbnail": thumbnail,
                "metadata": metadata
            })
        
        return images
        
    except Exception as e:
        logger.error(f"Error getting memory images: {e}")
        return []
    finally:
        conn.close()


def db_get_memories_for_current_date() -> List[Dict[str, Any]]:
    """
    Get memories that are relevant for the current date.
    (e.g., "On this day" memories from previous years)
    """
    try:
        # Get all memories and filter for current date relevance
        all_memories = db_generate_memories()
        
        current_date = datetime.now()
        current_month = current_date.month
        current_day = current_date.day
        
        relevant_memories = []
        
        for memory in all_memories:
            start_date = datetime.fromisoformat(memory["start_date"])
            
            # Check if memory is from same month/day but different year
            if start_date.month == current_month and abs(start_date.day - current_day) <= 7:
                years_ago = current_date.year - start_date.year
                if years_ago > 0:
                    memory["title"] = f"On This Day {years_ago} Year{'s' if years_ago > 1 else ''} Ago"
                    relevant_memories.append(memory)
        
        return relevant_memories
        
    except Exception as e:
        logger.error(f"Error getting memories for current date: {e}")
        return []
