"""
Database operations for Memories feature.
Handles creation, retrieval, and management of photo memories.
"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Type aliases
MemoryId = str
ImageId = str


def _connect() -> sqlite3.Connection:
    """Create database connection with foreign key enforcement."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_create_memories_table() -> None:
    """Create the memories table and related junction table."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        # Main memories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                location TEXT,
                latitude REAL,
                longitude REAL,
                cover_image_id TEXT,
                total_photos INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (cover_image_id) REFERENCES images(id) ON DELETE SET NULL
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

        # Index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_dates 
            ON memories(start_date, end_date)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_type 
            ON memories(memory_type)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_images_representative 
            ON memory_images(memory_id, is_representative)
            """
        )

        conn.commit()
        logger.info("Memories tables created successfully")

    except Exception as e:
        logger.error(f"Error creating memories tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def db_insert_memory(
    memory_id: str,
    title: str,
    memory_type: str,
    start_date: str,
    end_date: str,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    cover_image_id: Optional[str] = None,
    total_photos: int = 0,
) -> bool:
    """Insert a new memory into the database."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        created_at = datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO memories 
            (id, title, memory_type, start_date, end_date, location, 
             latitude, longitude, cover_image_id, total_photos, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                title,
                memory_type,
                start_date,
                end_date,
                location,
                latitude,
                longitude,
                cover_image_id,
                total_photos,
                created_at,
            ),
        )
        
        conn.commit()
        logger.info(f"Memory '{title}' created successfully with ID: {memory_id}")
        return True

    except Exception as e:
        logger.error(f"Error inserting memory: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_insert_memory_images(
    memory_id: str, 
    image_ids: List[str], 
    representative_ids: List[str] = None
) -> bool:
    """
    Link images to a memory.
    
    Args:
        memory_id: ID of the memory
        image_ids: List of all image IDs in this memory
        representative_ids: List of image IDs to mark as representative (for cards)
    """
    if not image_ids:
        return True

    representative_set = set(representative_ids) if representative_ids else set()
    
    conn = _connect()
    cursor = conn.cursor()

    try:
        records = [
            (memory_id, img_id, img_id in representative_set)
            for img_id in image_ids
        ]
        
        cursor.executemany(
            """
            INSERT OR IGNORE INTO memory_images 
            (memory_id, image_id, is_representative)
            VALUES (?, ?, ?)
            """,
            records,
        )
        
        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Error inserting memory images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_memories() -> List[Dict[str, Any]]:
    """Retrieve all memories with their representative images."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                m.id,
                m.title,
                m.memory_type,
                m.start_date,
                m.end_date,
                m.location,
                m.latitude,
                m.longitude,
                m.cover_image_id,
                m.total_photos,
                m.created_at,
                GROUP_CONCAT(
                    CASE WHEN mi.is_representative = 1 
                    THEN i.thumbnailPath END
                ) as representative_thumbnails
            FROM memories m
            LEFT JOIN memory_images mi ON m.id = mi.memory_id
            LEFT JOIN images i ON mi.image_id = i.id
            GROUP BY m.id
            ORDER BY m.start_date DESC
            """
        )

        results = cursor.fetchall()
        
        memories = []
        for row in results:
            thumbnails = row[11].split(',') if row[11] else []
            # Filter out None values
            thumbnails = [t for t in thumbnails if t]
            
            memories.append({
                "id": row[0],
                "title": row[1],
                "memory_type": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "location": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "cover_image_id": row[8],
                "total_photos": row[9],
                "created_at": row[10],
                "representative_thumbnails": thumbnails,
            })

        return memories

    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        return []
    finally:
        conn.close()


def db_get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific memory with all its images."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        # Get memory details
        cursor.execute(
            """
            SELECT 
                id, title, memory_type, start_date, end_date,
                location, latitude, longitude, cover_image_id,
                total_photos, created_at
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )

        memory_row = cursor.fetchone()
        if not memory_row:
            return None

        # Get all images in this memory
        cursor.execute(
            """
            SELECT 
                i.id, i.path, i.thumbnailPath, i.metadata,
                mi.is_representative
            FROM memory_images mi
            JOIN images i ON mi.image_id = i.id
            WHERE mi.memory_id = ?
            ORDER BY i.path
            """,
            (memory_id,),
        )

        images = []
        for img_row in cursor.fetchall():
            from app.utils.images import image_util_parse_metadata
            
            images.append({
                "id": img_row[0],
                "path": img_row[1],
                "thumbnailPath": img_row[2],
                "metadata": image_util_parse_metadata(img_row[3]),
                "is_representative": bool(img_row[4]),
            })

        return {
            "id": memory_row[0],
            "title": memory_row[1],
            "memory_type": memory_row[2],
            "start_date": memory_row[3],
            "end_date": memory_row[4],
            "location": memory_row[5],
            "latitude": memory_row[6],
            "longitude": memory_row[7],
            "cover_image_id": memory_row[8],
            "total_photos": memory_row[9],
            "created_at": memory_row[10],
            "images": images,
        }

    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {e}")
        return None
    finally:
        conn.close()


def db_delete_memory(memory_id: str) -> bool:
    """Delete a memory (cascade will remove memory_images entries)."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Memory {memory_id} deleted successfully")
            return True
        return False

    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_clear_all_memories() -> bool:
    """Clear all memories from the database."""
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM memories")
        conn.commit()
        logger.info("All memories cleared from database")
        return True

    except Exception as e:
        logger.error(f"Error clearing memories: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()