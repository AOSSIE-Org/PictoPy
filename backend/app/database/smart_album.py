import sqlite3
import json
import time
import uuid
from typing import List, Optional, Dict
from app.database.connection import get_db_connection
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def db_create_smart_albums_table():
    """Create the smart_albums table"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS smart_albums (
                album_id TEXT PRIMARY KEY,
                thumb_image_id TEXT,
                album_name TEXT NOT NULL,
                album_type TEXT NOT NULL,
                criteria TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                auto_update boolean DEFAULT 1,
                image_count INTEGER DEFAULT 0,
                FOREIGN KEY (thumb_image_id) REFERENCES images(id)
            );

            CREATE TABLE IF NOT EXISTS smart_album_images (
                album_id TEXT,
                image_id TEXT,
                added_at INTEGER NOT NULL,
                PRIMARY KEY (album_id, image_id),
                FOREIGN KEY (album_id) REFERENCES smart_albums(album_id) ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_smart_album_images_album ON smart_album_images(album_id);
            CREATE INDEX IF NOT EXISTS idx_smart_album_images_image ON smart_album_images(image_id);
            CREATE INDEX IF NOT EXISTS idx_smart_albums_type ON smart_albums(album_type);
        """
        )
        logger.info("Smart albums tables created successfully")



def db_create_smart_album(
    album_name: str,
    album_type: str,
    criteria: Dict,
    auto_update: bool = True
) -> str:
    """Create a new smart album and return its ID"""
    album_id = str(uuid.uuid4())
    timestamp = int(time.time())
    criteria_json = json.dumps(criteria)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO smart_albums (
                album_id, album_name, album_type, criteria,
                created_at, updated_at, auto_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (album_id, album_name, album_type, criteria_json, timestamp, timestamp, int(auto_update))
        )
        conn.commit()

    logger.info(f"Smart album '{album_name}' created with ID: {album_id}")
    return album_id

def db_get_all_smart_albums() -> List[Dict]:
    """Get all smart albums with metadata"""
    with get_db_connection() as conn:
        conn.row_factory=sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
              sa.*,
              COUNT(sai.image_id) as image_count
            FROM smart_albums sa
            LEFT JOIN smart_album_images sai ON sa.album_id = sai.album_id
            GROUP BY sa.album_id
            ORDER BY sa.created_at DESC
        """)
        albums=[dict(row) for row in cursor.fetchall()]
    for album in albums:
        album['criteria'] = json.loads(album['criteria'])


    return albums

def db_get_smart_album_by_id(album_id: str) -> Optional[Dict]:
    """Get a smart album by its ID"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                sa.*,
                COUNT(sai.image_id) as image_count
            FROM smart_albums sa
            LEFT JOIN smart_album_images sai ON sa.album_id = sai.album_id
            WHERE sa.album_id = ?
            GROUP BY sa.album_id
            
            
         """, (album_id,))
        row = cursor.fetchone()
        if row:
            album = dict(row)
            album['criteria'] = json.loads(album['criteria'])
            return album
        return None
    
def db_add_images_to_smart_album(album_id: str, image_ids: List[str]):
    """Add multiple images to a smart album"""
    if not image_ids:
        return
    current_time = int(time.time())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        data=[(album_id, image_id, current_time) for image_id in image_ids]
        cursor.executemany(
            """
            INSERT OR IGNORE INTO smart_album_images (album_id, image_id, added_at)
            VALUES (?, ?, ?)
            """,
            data
        )
        #Update album timestamp
        cursor.execute(
            """
            UPDATE smart_albums
            SET updated_at = ?
            WHERE album_id = ?
            """,
            (current_time, album_id)
        )
    logger.info(f"Added {len(image_ids)} images to smart album {album_id}") 

def db_remove_images_from_smart_album(album_id: str, image_ids: List[str]):
    """Remove images from a smart album"""
    if not image_ids:
        return
    with get_db_connection() as conn:
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in image_ids)
        cursor.execute(
            f"""
            DELETE FROM smart_album_images
            WHERE album_id = ? AND image_id IN ({placeholders})
            """,
            (album_id, *image_ids)
        )
    logger.info(f"Removed {len(image_ids)} images from smart album {album_id}")

def db_get_images_for_smart_album(album_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get images for a specific smart album with pagination"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT
                i.*,
                sai.added_at as album_added_at
                FROM smart_album_images sai
                JOIN images i ON sai.image_id = i.id
                WHERE sai.album_id = ?
                ORDER BY sai.added_at DESC
                """
        params = [album_id]
        if limit > 0:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cursor.execute(query, params)
        images = [dict(row) for row in cursor.fetchall()]
    return images

def db_find_images_by_criteria(criteria: Dict) -> List[str]:
    """
    Find images matching smart album criteria.
    Criteria format:
    {
        "type": "object" | "face" | "scene" | "custom",
        "class_ids": [1, 2, 3],  # For object detection
        "class_names": ["dog", "cat"],  # Alternative to class_ids
        "face_id": "uuid",  # For face albums
        "date_range": {"start": timestamp, "end": timestamp},
        "min_confidence": 0.6
    }
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query_parts = ["SELECT DISTINCT i.id FROM images i"]
        conditions = []
        params = []
        
        album_type = criteria.get("type")
        if album_type == "object":
            # Join with image_classes and mappings
            query_parts.append("JOIN image_classes ic ON i.id = ic.image_id")
            query_parts.append("JOIN mappings m ON ic.class_id = m.class_id")
            
            if "class_ids" in criteria:
                placeholders = ','.join('?' * len(criteria["class_ids"]))
                conditions.append(f"ic.class_id IN ({placeholders})")
                params.extend(criteria["class_ids"])
            
            if "class_names" in criteria:
                placeholders = ','.join('?' * len(criteria["class_names"]))
                conditions.append(f"m.name IN ({placeholders})")
                params.extend(criteria["class_names"])
        
        elif album_type == "face":
            # Join with face_embeddings
            query_parts.append("JOIN face_embeddings fe ON i.id = fe.image_id")
            
            if "face_id" in criteria:
                conditions.append("fe.face_id = ?")
                params.append(criteria["face_id"])

         # Date range filter
        if "date_range" in criteria:
            if "start" in criteria["date_range"]:
                conditions.append("i.creation_time >= ?")
                params.append(criteria["date_range"]["start"])
            if "end" in criteria["date_range"]:
                conditions.append("i.creation_time <= ?")
                params.append(criteria["date_range"]["end"])
        
        # Combine query
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query = " ".join(query_parts)
        
        cursor.execute(query, params)
        image_ids = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"Found {len(image_ids)} images matching criteria")
    return image_ids

def db_delete_smart_album(album_id: str):
    """Delete a smart album (cascade will remove album_images entries)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM smart_albums WHERE album_id = ?", (album_id,))
    
    logger.info(f"Deleted smart album {album_id}")

def db_update_smart_album(album_id: str, album_name: str = None, auto_update: bool = None):
    """Update smart album properties"""
    updates = []
    params = []
    
    if album_name is not None:
        updates.append("album_name = ?")
        params.append(album_name)
    
    if auto_update is not None:
        updates.append("auto_update = ?")
        params.append(auto_update)
    
    if updates:
        updates.append("updated_at = ?")
        params.append(int(time.time()))
        params.append(album_id)
        
        query = f"UPDATE smart_albums SET {', '.join(updates)} WHERE album_id = ?"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()


def db_clear_smart_album_images(album_id: str):
    """Remove all images from a smart album (used before refresh)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM smart_album_images WHERE album_id = ?", (album_id,))
        conn.commit()
    
    logger.info(f"Cleared all images from album {album_id}")