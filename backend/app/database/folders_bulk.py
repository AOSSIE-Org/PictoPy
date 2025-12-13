# Database helpers for bulk operations
import sqlite3
from typing import List, Dict, Any
from .connection import get_db_connection

def db_count_images_in_folder(folder_id: str) -> int:
    """
    Count total images in a folder.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM images WHERE folder_id = ?",
            (folder_id,)
        )
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

def db_count_tagged_images_in_folder(folder_id: str) -> int:
    """
    Count images that have been AI tagged in a folder.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT COUNT(DISTINCT i.id)
            FROM images i
            JOIN tags t ON i.id = t.image_id
            WHERE i.folder_id = ?
            """,
            (folder_id,)
        )
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

def db_get_folders_summary() -> Dict[str, Dict[str, Any]]:
    """
    Get summary statistics for all folders.
    Optimized single-query approach.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            f.id as folder_id,
            f.name as folder_name,
            f.ai_tagging_enabled,
            COUNT(DISTINCT i.id) as total_images,
            COUNT(DISTINCT CASE WHEN t.id IS NOT NULL THEN i.id END) as tagged_images
        FROM folders f
        LEFT JOIN images i ON f.id = i.folder_id
        LEFT JOIN tags t ON i.id = t.image_id
        GROUP BY f.id, f.name, f.ai_tagging_enabled
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        summary = {}
        for row in rows:
            folder_id = row['folder_id']
            total = row['total_images']
            tagged = row['tagged_images']
            
            if total == 0:
                status = 'empty'
                progress = 0.0
            elif tagged == total:
                status = 'completed'
                progress = 100.0
            elif tagged > 0:
                status = 'in_progress'
                progress = (tagged / total) * 100
            else:
                status = 'pending'
                progress = 0.0
            
            summary[folder_id] = {
                'folder_name': row['folder_name'],
                'ai_tagging_enabled': bool(row['ai_tagging_enabled']),
                'total_images': total,
                'tagged_images': tagged,
                'status': status,
                'progress_percentage': round(progress, 2)
            }
        
        return summary
    finally:
        conn.close()

def db_bulk_enable_tagging(folder_ids: List[str]) -> int:
    """
    Enable AI tagging for multiple folders at once.
    Returns number of folders updated.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ','.join('?' * len(folder_ids))
        query = f"""
        UPDATE folders 
        SET ai_tagging_enabled = 1
        WHERE id IN ({placeholders})
        """
        
        cursor.execute(query, folder_ids)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
