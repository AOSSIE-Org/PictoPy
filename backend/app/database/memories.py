import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.config.settings import DATABASE_PATH

# Type definitions
MemoryId = str


def db_create_memories_table() -> None:
    """Create the memories table if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                date_range_start TEXT NOT NULL,
                date_range_end TEXT NOT NULL,
                location_name TEXT,
                latitude REAL,
                longitude REAL,
                image_ids TEXT NOT NULL,
                representative_image_id TEXT,
                created_at TEXT NOT NULL,
                year INTEGER NOT NULL,
                CHECK (memory_type IN ('on_this_day', 'trip', 'date_range'))
            )
        """
        )
        
        # Create index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_year 
            ON memories(year)
            """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_type 
            ON memories(memory_type)
            """
        )
        
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def db_insert_memory(memory_data: Dict[str, Any]) -> MemoryId:
    """
    Insert a new memory into the database.
    
    Args:
        memory_data: Dictionary containing memory information
        
    Returns:
        The memory_id of the inserted memory
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO memories (
                memory_id, title, memory_type, date_range_start, date_range_end,
                location_name, latitude, longitude, image_ids, 
                representative_image_id, created_at, year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_data["memory_id"],
                memory_data["title"],
                memory_data["memory_type"],
                memory_data["date_range_start"],
                memory_data["date_range_end"],
                memory_data.get("location_name"),
                memory_data.get("latitude"),
                memory_data.get("longitude"),
                memory_data["image_ids"],
                memory_data.get("representative_image_id"),
                memory_data["created_at"],
                memory_data["year"],
            ),
        )
        conn.commit()
        return memory_data["memory_id"]
    finally:
        conn.close()


def db_get_all_memories() -> List[Dict[str, Any]]:
    """
    Retrieve all memories from the database.
    
    Returns:
        List of memory dictionaries
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT memory_id, title, memory_type, date_range_start, date_range_end,
                   location_name, latitude, longitude, image_ids, 
                   representative_image_id, created_at, year
            FROM memories
            ORDER BY date_range_start DESC
            """
        )
        
        rows = cursor.fetchall()
        memories = []
        
        for row in rows:
            memories.append({
                "memory_id": row[0],
                "title": row[1],
                "memory_type": row[2],
                "date_range_start": row[3],
                "date_range_end": row[4],
                "location_name": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "image_ids": row[8],
                "representative_image_id": row[9],
                "created_at": row[10],
                "year": row[11],
            })
        
        return memories
    finally:
        conn.close()


def db_get_memory_by_id(memory_id: MemoryId) -> Optional[Dict[str, Any]]:
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: The ID of the memory to retrieve
        
    Returns:
        Memory dictionary or None if not found
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT memory_id, title, memory_type, date_range_start, date_range_end,
                   location_name, latitude, longitude, image_ids, 
                   representative_image_id, created_at, year
            FROM memories
            WHERE memory_id = ?
            """,
            (memory_id,),
        )
        
        row = cursor.fetchone()
        
        if row:
            return {
                "memory_id": row[0],
                "title": row[1],
                "memory_type": row[2],
                "date_range_start": row[3],
                "date_range_end": row[4],
                "location_name": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "image_ids": row[8],
                "representative_image_id": row[9],
                "created_at": row[10],
                "year": row[11],
            }
        
        return None
    finally:
        conn.close()


def db_delete_all_memories() -> int:
    """
    Delete all memories from the database.
    
    Returns:
        Number of memories deleted
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM memories")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def db_delete_memory(memory_id: MemoryId) -> bool:
    """
    Delete a specific memory.
    
    Args:
        memory_id: The ID of the memory to delete
        
    Returns:
        True if deleted, False otherwise
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
