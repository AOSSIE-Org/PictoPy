from fastapi import APIRouter, BackgroundTasks
from app.models.celebrity_detection.CelebrityMatcher import CelebrityMatcher
from app.database.faces import db_get_all_faces_with_cluster_names, db_update_face_cluster_ids_batch
from app.database.face_clusters import db_get_or_create_cluster_by_name
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

def process_celebrity_scan():
    try:
        logger.info("Starting background celebrity scan...")
        matcher = CelebrityMatcher()
        faces = db_get_all_faces_with_cluster_names()
        logger.info(f"Scanning {len(faces)} faces for celebrity matches...")
        
        updates = []
        matches_found = 0
        for face in faces:
            embeddings = face["embeddings"]
            
            # Identify face
            name = matcher.identify_face(embeddings)
            
            if name:
                matches_found += 1
                # Check if already named correctly
                current_name = face.get("cluster_name")
                
                # If current name is different (or None), calculate cluster ID and queue update
                if current_name != name:
                    cluster_id = db_get_or_create_cluster_by_name(name)
                    updates.append({"face_id": face["face_id"], "cluster_id": cluster_id})
                    logger.debug(f"Face {face['face_id']} matched as {name}. Queued for update.")
        
        if updates:
            db_update_face_cluster_ids_batch(updates)
            logger.info(f"Successfully updated {len(updates)} faces with celebrity names.")
        else:
            logger.info(f"Scan complete. Found {matches_found} matches, but no updates were needed.")

    except Exception as e:
        logger.error(f"Error during celebrity scan: {e}")

@router.post("/scan")
def scan_celebrities(background_tasks: BackgroundTasks):
    """
    Triggers a background scan of all existing faces to identify celebrities.
    """
    background_tasks.add_task(process_celebrity_scan)
    return {"message": "Celebrity scan started in background."}
