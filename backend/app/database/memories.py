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
            ORDER BY CASE 
                WHEN json_valid(metadata) THEN json_extract(metadata, '$.date_created') 
                ELSE NULL 
            END DESC, id DESC
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
                
                # Normalize to date-only to avoid timezone issues
                date_only = date_obj.date()
            except Exception as e:
                logger.warning(f"Could not parse date {date_created}: {e}")
                continue
            
            location = metadata.get("location", "Unknown Location")
            latitude = metadata.get("latitude")
            longitude = metadata.get("longitude")
            
            # Create grouping key (year-month + location)
            date_key = date_only.strftime("%Y-%m")
            
            # Group by similar locations (or "Unknown")
            loc_key = location if location != "Unknown Location" else "no_location"
            
            group_key = f"{date_key}_{loc_key}"
            
            memories_by_group[group_key].append({
                "id": image_id,
                "path": path,
                "thumbnail": thumbnail,
                "date": date_only.isoformat(),
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "metadata": metadata
            })
        
        # Generate memory objects
        memories = []
        current_date = datetime.now().date()  # Normalize to date-only
        
        for group_key, images_in_group in memories_by_group.items():
            if len(images_in_group) < 3:  # Skip groups with too few images
                continue
                
            # Sort images by date (date is now ISO string)
            images_in_group.sort(key=lambda x: x["date"])
            
            # Parse first and last dates for memory metadata (date-only strings)
            first_date = datetime.strptime(images_in_group[0]["date"], "%Y-%m-%d").date()
            last_date = datetime.strptime(images_in_group[-1]["date"], "%Y-%m-%d").date()
            location = images_in_group[0]["location"]
            
            # Calculate time difference using date objects
            years_ago = current_date.year - first_date.year
            
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
        
        # Persist memories to database (best-effort, atomic refresh)
        try:
            # Ensure tables exist
            db_create_memories_table()
            
            # Begin atomic transaction
            cursor.execute("BEGIN IMMEDIATE")
            
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
            logger.error(f"Error persisting memories (continuing with in-memory data): {e}")
            conn.rollback()
            # Don't re-raise - treat persistence as best-effort
        
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
            ORDER BY CASE 
                WHEN json_valid(i.metadata) THEN json_extract(i.metadata, '$.date_created') 
                ELSE NULL 
            END ASC, i.id ASC
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
    Queries the persisted memories table instead of regenerating.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        current_date = datetime.now().date()  # Normalize to date-only
        current_month = current_date.month
        current_day = current_date.day
        
        # Query persisted memories matching current month with +/-7 day window
        cursor.execute(
            """
            SELECT id, title, description, start_date, end_date, location, 
                   latitude, longitude, image_count
            FROM memories
            WHERE CAST(strftime('%m', start_date) AS INTEGER) = ?
            AND ABS(CAST(strftime('%d', start_date) AS INTEGER) - ?) <= 7
            AND CAST(strftime('%Y', start_date) AS INTEGER) < ?
            ORDER BY start_date DESC
            """,
            (current_month, current_day, current_date.year)
        )
        
        rows = cursor.fetchall()
        
        if not rows:
            # Fallback: try regenerating if cache is empty
            logger.info("No memories found in cache, regenerating...")
            db_generate_memories()
            # Retry query after regeneration
            cursor.execute(
                """
                SELECT id, title, description, start_date, end_date, location, 
                       latitude, longitude, image_count
                FROM memories
                WHERE CAST(strftime('%m', start_date) AS INTEGER) = ?
                AND ABS(CAST(strftime('%d', start_date) AS INTEGER) - ?) <= 7
                AND CAST(strftime('%Y', start_date) AS INTEGER) < ?
                ORDER BY start_date DESC
                """,
                (current_month, current_day, current_date.year)
            )
            rows = cursor.fetchall()
        
        relevant_memories = []
        
        for row in rows:
            memory_id, title, description, start_date_str, end_date_str, location, latitude, longitude, image_count = row
            
            # Parse start date to calculate years ago (date-only string)
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            years_ago = current_date.year - start_date.year
            
            # Get representative images for this memory
            cursor.execute(
                """
                SELECT i.id, i.path, i.thumbnailPath, i.metadata
                FROM images i
                JOIN memory_images mi ON i.id = mi.image_id
                WHERE mi.memory_id = ? AND mi.is_representative = 1
                ORDER BY CASE 
                    WHEN json_valid(i.metadata) THEN json_extract(i.metadata, '$.date_created') 
                    ELSE NULL 
                END ASC, i.id ASC
                LIMIT 5
                """,
                (memory_id,)
            )
            
            images = []
            from app.utils.images import image_util_parse_metadata
            
            for img_row in cursor.fetchall():
                image_id, path, thumbnail, metadata_str = img_row
                metadata = image_util_parse_metadata(metadata_str)
                
                # Extract date from metadata
                date_created = metadata.get("date_created", start_date_str)
                
                images.append({
                    "id": image_id,
                    "path": path,
                    "thumbnail": thumbnail,
                    "date": date_created,
                    "location": metadata.get("location"),
                    "latitude": metadata.get("latitude"),
                    "longitude": metadata.get("longitude"),
                    "metadata": metadata
                })
            
            # Create a shallow copy to avoid mutating cached DB rows
            memory_copy = {
                "id": memory_id,
                "title": f"On This Day {years_ago} Year{'s' if years_ago > 1 else ''} Ago",
                "description": description,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "image_count": image_count,
                "images": images
            }
            
            relevant_memories.append(memory_copy)
        
        return relevant_memories
        
    except Exception as e:
        logger.error(f"Error getting memories for current date: {e}")
        return []
    finally:
        conn.close()
