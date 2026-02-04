import json
import numpy as np
import sqlite3
from typing import List, Dict, Any
from app.database.images import _connect
from app.models.ClipModel import ClipModel
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Singleton instance of ClipModel
_clip_model = None

def get_clip_model():
    global _clip_model
    if _clip_model is None:
        _clip_model = ClipModel()
    return _clip_model

def generate_and_store_embedding(image_id: str, image_path: str) -> bool:
    """
    Generates a CLIP embedding for an image and stores it in the database.
    """
    try:
        model = get_clip_model()
        embedding = model.get_embedding(image_path)
        
        if embedding is None:
            return False
            
        # Convert numpy array to JSON string for storage
        embedding_json = json.dumps(embedding.tolist())
        
        conn = _connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE images SET clip_embedding = ? WHERE id = ?",
            (embedding_json, image_id)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error storing embedding for image {image_id}: {e}")
        return False

def find_similar_images(target_image_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Finds images similar to the target image using cosine similarity of CLIP embeddings.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        # Get target embedding
        cursor.execute("SELECT clip_embedding FROM images WHERE id = ?", (target_image_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            # If embedding doesn't exist, try to generate it
            cursor.execute("SELECT path FROM images WHERE id = ?", (target_image_id,))
            path_result = cursor.fetchone()
            if path_result:
                success = generate_and_store_embedding(target_image_id, path_result[0])
                if not success:
                    return []
                # Fetch again
                cursor.execute("SELECT clip_embedding FROM images WHERE id = ?", (target_image_id,))
                result = cursor.fetchone()
                if not result or not result[0]:
                    return []
            else:
                return []

        target_embedding = np.array(json.loads(result[0]))
        return _search_by_embedding(target_embedding, limit, exclude_id=target_image_id)
        
    except Exception as e:
        logger.error(f"Error in find_similar_images: {e}")
        return []
    finally:
        conn.close()

def find_images_by_text(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Finds images matching a text query using semantic similarity.
    """
    try:
        model = get_clip_model()
        text_embedding = model.get_text_embedding(query)
        
        if text_embedding is None:
            return []
            
        return _search_by_embedding(text_embedding, limit)
    except Exception as e:
        logger.error(f"Error in find_images_by_text: {e}")
        return []

def _search_by_embedding(target_embedding: np.ndarray, limit: int = 20, exclude_id: str = None) -> List[Dict[str, Any]]:
    """
    Helper function to search for images by an embedding.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        # Get all other embeddings
        query = "SELECT id, clip_embedding FROM images WHERE clip_embedding IS NOT NULL"
        params = []
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        similarities = []
        
        for img_id, emb_json in rows:
            try:
                emb = np.array(json.loads(emb_json))
                # Calculate Cosine Similarity
                similarity = np.dot(target_embedding, emb) / (np.linalg.norm(target_embedding) * np.linalg.norm(emb))
                similarities.append((img_id, similarity))
            except Exception:
                continue
                
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_matches = similarities[:limit]
        
        if not top_matches:
            return []
            
        matched_ids = [m[0] for m in top_matches]
        placeholders = ",".join("?" for _ in matched_ids)
        
        cursor.execute(
            f"SELECT id, path, thumbnailPath, metadata, isFavourite FROM images WHERE id IN ({placeholders})",
            matched_ids
        )
        
        image_details = {row[0]: row for row in cursor.fetchall()}
        
        final_results = []
        for img_id, score in top_matches:
            if img_id in image_details:
                row = image_details[img_id]
                final_results.append({
                    "id": row[0],
                    "path": row[1],
                    "thumbnailPath": row[2],
                    "metadata": row[3],
                    "isFavourite": bool(row[4]),
                    "similarityScore": float(score)
                })
                
        return final_results
    finally:
        conn.close()

def index_all_images() -> int:
    """
    Generates embeddings for all images that don't have them.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, path FROM images WHERE clip_embedding IS NULL")
        images = cursor.fetchall()
        
        if not images:
            return 0
            
        logger.info(f"Indexing {len(images)} images...")
        count = 0
        for img_id, path in images:
            if generate_and_store_embedding(img_id, path):
                count += 1
        
        logger.info(f"Indexing complete. Generated {count} embeddings.")
        return count
    finally:
        conn.close()

def get_indexing_status() -> Dict[str, int]:
    """
    Returns the count of indexed and unindexed images.
    """
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM images WHERE clip_embedding IS NOT NULL")
        indexed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images WHERE clip_embedding IS NULL")
        unindexed = cursor.fetchone()[0]
        
        return {
            "indexed": indexed,
            "unindexed": unindexed,
            "total": indexed + unindexed
        }
    finally:
        conn.close()
