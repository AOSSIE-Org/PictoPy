# Standard library imports
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime

# App-specific imports
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def db_create_memories_table() -> None:
    """Create the memories table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                memory_type TEXT NOT NULL,
                date_range_start TEXT NOT NULL,
                date_range_end TEXT NOT NULL,
                location TEXT,
                latitude REAL,
                longitude REAL,
                image_count INTEGER DEFAULT 0,
                cover_image_id TEXT,
                created_at TEXT NOT NULL,
                last_shown_at TEXT,
                FOREIGN KEY (cover_image_id) REFERENCES images(id) ON DELETE SET NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_date
            ON memories(date_range_start, date_range_end)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_location
            ON memories(location)
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_images (
                memory_id TEXT,
                image_id TEXT,
                position INTEGER DEFAULT 0,
                PRIMARY KEY (memory_id, image_id),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
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


def db_create_memory(memory_data: Dict[str, Any]) -> bool:
    """Create a new memory in the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO memories 
            (id, title, description, memory_type, date_range_start, date_range_end,
             location, latitude, longitude, image_count, cover_image_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory_data["id"],
                memory_data["title"],
                memory_data.get("description"),
                memory_data["memory_type"],
                memory_data["date_range_start"],
                memory_data["date_range_end"],
                memory_data.get("location"),
                memory_data.get("latitude"),
                memory_data.get("longitude"),
                memory_data.get("image_count", 0),
                memory_data.get("cover_image_id"),
                memory_data.get("created_at", datetime.now().isoformat()),
            ),
        )

        if "image_ids" in memory_data and memory_data["image_ids"]:
            for idx, image_id in enumerate(memory_data["image_ids"]):
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO memory_images (memory_id, image_id, position)
                    VALUES (?, ?, ?)
                """,
                    (memory_data["id"], image_id, idx),
                )

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_get_all_memories(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all memories from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        query = """
            SELECT 
                m.id, m.title, m.description, m.memory_type,
                m.date_range_start, m.date_range_end,
                m.location, m.latitude, m.longitude,
                m.image_count, m.cover_image_id,
                m.created_at, m.last_shown_at,
                GROUP_CONCAT(mi.image_id) as image_ids
            FROM memories m
            LEFT JOIN memory_images mi ON m.id = mi.memory_id
            GROUP BY m.id
            ORDER BY m.date_range_start DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            memory = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "memory_type": row[3],
                "date_range_start": row[4],
                "date_range_end": row[5],
                "location": row[6],
                "latitude": row[7],
                "longitude": row[8],
                "image_count": row[9],
                "cover_image_id": row[10],
                "created_at": row[11],
                "last_shown_at": row[12],
                "image_ids": row[13].split(",") if row[13] else [],
            }
            memories.append(memory)

        return memories
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        return []
    finally:
        conn.close()


def db_get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific memory by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                m.id, m.title, m.description, m.memory_type,
                m.date_range_start, m.date_range_end,
                m.location, m.latitude, m.longitude,
                m.image_count, m.cover_image_id,
                m.created_at, m.last_shown_at,
                GROUP_CONCAT(mi.image_id) as image_ids
            FROM memories m
            LEFT JOIN memory_images mi ON m.id = mi.memory_id
            WHERE m.id = ?
            GROUP BY m.id
        """,
            (memory_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "memory_type": row[3],
            "date_range_start": row[4],
            "date_range_end": row[5],
            "location": row[6],
            "latitude": row[7],
            "longitude": row[8],
            "image_count": row[9],
            "cover_image_id": row[10],
            "created_at": row[11],
            "last_shown_at": row[12],
            "image_ids": row[13].split(",") if row[13] else [],
        }
    except Exception as e:
        logger.error(f"Error fetching memory {memory_id}: {e}")
        return None
    finally:
        conn.close()


def db_update_memory_last_shown(memory_id: str) -> bool:
    """Update the last_shown_at timestamp for a memory."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE memories SET last_shown_at = ? WHERE id = ?",
            (datetime.now().isoformat(), memory_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating memory last_shown: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def db_delete_memory(memory_id: str) -> bool:
    """Delete a memory from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
